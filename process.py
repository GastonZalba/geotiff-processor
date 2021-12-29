import sys
import os
import secrets
import shutil
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import params as params
import tempfile
from osgeo_utils.gdal_calc import Calc
from PIL import Image, ImageChops, ImageEnhance

from version import __version__

try:
    from osgeo import gdal, osr, ogr
except:
    sys.exit('ERROR: osgeo module was not found')

TEMP_FOLDER = tempfile.gettempdir()


def removeExtension(filename):
    return os.path.splitext(filename)[0]


class ConvertGeotiff:
    '''
    Some helpful docs:
    https://pcjericks.github.io/py-gdalogr-cookbook/
    https://docs.geoserver.geo-solutions.it/edu/en/raster_data/advanced_gdal/example5.html
    https://gdal.org/tutorials/raster_api_tut.html
    https://gdal.org/python/osgeo.gdal-module.html
    https://gdal.org/api/python.html

    '''

    def __init__(self):
        print(f'SCRIPT Version: {__version__}')

        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print(f'GDAL Version: {version_num}')

        # Allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')
        self.isMDE = False
        self.checkDirectories()
        self.processTifs()

    def checkDirectories(self):
        '''
        Create folders if no exists
        '''

        if params.clean_output_folder:
            if os.path.exists(params.output_folder):
                shutil.rmtree(Path(params.output_folder))

        Path(params.geoserver['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.storage['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.storagePreview['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.storageJSONdata['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.outlines['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.geoserverMDE['output_folder']).mkdir(
            parents=True, exist_ok=True)

    def processTifs(self):

        # Find all .tif extensions in the inout folder
        for subdir, dirs, files in os.walk(params.input_folder):
            for file in files:
                filepath = subdir + os.sep + file

                if (file.endswith(".tif") | file.endswith(".tiff")):
                    try:
                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                    except RuntimeError as e:
                        print('Unable to open {}'.format(filepath))
                        print(e)
                        sys.exit(1)

                ok = params.filename_prefix in file

                # Number of bands
                self.bandas = file_ds.RasterCount
                self.ultimaBanda = file_ds.GetRasterBand(self.bandas)
                self.tieneCanalAlfa = (
                    self.ultimaBanda.GetColorInterpretation() == 6)  # https://github.com/rasterio/rasterio/issues/100
                self.noDataValue = self.ultimaBanda.GetNoDataValue()  # take any band

                self.isMDE = self.bandas <= 2

                # Random hash to be used as the map id
                # https://docs.python.org/3/library/secrets.html

                if(self.isMDE):    # Generating output filename for DME case
                    self.mapId = removeExtension(file.split(
                        params.filename_prefix)[1].split(params.filename_suffix)[0]) if ok else secrets.token_hex(nbytes=6)

                    self.registroid = file.split(
                        params.filename_prefix)[0] if ok else self.cleanFilename(removeExtension(file.split(params.filename_suffix)[0]))
                else:
                    self.mapId = removeExtension(
                        file.split(params.filename_prefix)[1]) if ok else secrets.token_hex(nbytes=6)

                    self.registroid = file.split(
                        "_")[0] if ok else self.cleanFilename(removeExtension(file))

                self.output = f'{self.registroid}{params.filename_prefix}{self.mapId}'
                self.outputFilename = self.output if not self.isMDE else '{}{}'.format(
                    self.output, params.filename_suffix)

                # File GSD
                gt = file_ds.GetGeoTransform()
                self.pixelSizeX = gt[1]
                self.pixelSizeY = -gt[5]

                # file's GSD: get average x and y values
                self.original_gsd = round(
                    (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

                # File Projection
                prj = file_ds.GetProjection()
                srs = osr.SpatialReference(wkt=prj)
                self.epsg = int(srs.GetAttrValue('AUTHORITY', 1))

                # Drone Deploy | Pix4DMatic dates
                self.date = self.getDate(file_ds)

                self.extra_metadata = params.metadata

                self.extra_metadata.append(
                    'registroId={}'.format(self.registroid))

                self.extra_metadata.append('mapId={}'.format(self.mapId))

                print('Exporting storage files...')
                self.exportStorageFiles(file_ds)

                print('Exporting geoserver files...')
                self.exportGeoserverFiles(file_ds, file)
                # Once we're done, close properly the dataset
                file_ds = None

                print('--> Operation finished')

    def cleanFilename(self, filename):
        '''
        Check if the filename has a dash and a version number. This occurs when
        there are multiples maps in one registro.está hecho todo bien
        Returns only the registtroid
        '''
        filename = filename.split('-')[0]

        return filename

    def getDate(self, file_ds):
        droneDeployDate = file_ds.GetMetadataItem("acquisitionStartDate")
        pix4DMaticDate = file_ds.GetMetadataItem("TIFFTAG_DATETIME")
        # pix4dMapper doesn't store date info? WTF

        if droneDeployDate:
            return datetime.strptime(droneDeployDate[:-6], "%Y-%m-%dT%H:%M:%S")
        elif pix4DMaticDate:
            return datetime.strptime(pix4DMaticDate, "%Y:%m:%d %H:%M:%S")
        else:
            return None

    def exportGeoserverFiles(self, file_ds, file):

        tmpWarp = None

        print('Converting {}...'.format(file))

        ds = None

        # if file has diferent epsg
        if (self.epsg != params.geoserver['epsg']):

            kwargs = {
                'format': 'GTiff',
                'xRes': params.geoserver['gsd']/100,
                'yRes': params.geoserver['gsd']/100,
                'srcSRS': 'EPSG:{}'.format(self.epsg),
                'multithread': True,
                'dstSRS': 'EPSG:{}'.format(params.geoserver['epsg']),
                # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
                'srcNodata': 'none' if self.tieneCanalAlfa else self.noDataValue
            }

            tmpWarp = TEMP_FOLDER + "\\" + file
            print('Converting EPSG:{} to EPSG:{}'.format(
                self.epsg, params.geoserver['epsg']))
            # https://gis.stackexchange.com/questions/260502/using-gdalwarp-to-generate-a-binary-mask
            ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

        outputFilename = '{}.tif'.format(self.outputFilename)

        gdaloutput = params.geoserver['output_folder'] if not self.isMDE else params.geoserverMDE['output_folder']
        gdaloutput = '{}/{}'.format(gdaloutput, outputFilename)

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3] if not self.isMDE else [1],
            'xRes': params.geoserver['gsd']/100,
            'yRes': params.geoserver['gsd']/100,
            'creationOptions': params.geoserver['creationOptions'] if not self.isMDE else params.geoserverMDE['creationOptions'],
            'metadataOptions': self.extra_metadata,
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none' if self.tieneCanalAlfa else self.noDataValue
        }

        if(not self.isMDE):
            kwargs['maskBand'] = 4

        fileToConvert = ds if tmpWarp else file_ds

        if (params.outlines['enabled'] and not self.isMDE):
            self.exportOutline(fileToConvert)

        ds = gdal.Translate(gdaloutput, fileToConvert, **kwargs)

        if (params.geoserver['overviews']):
            self.createOverviews(ds)

        ds = None

        # Delete tmp files
        if tmpWarp:
            del tmpWarp

    def exportStorageFiles(self, filepath):
        '''
        Export high and low res files
        '''

        outputFilename = '{}.tif'.format(self.outputFilename)

        gdaloutput = params.storage['output_folder']

        gdaloutput = '{}/{}'.format(
            gdaloutput, outputFilename)

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3] if not self.isMDE else [1],
            'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
            'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
            'creationOptions': params.storage['creationOptions'] if not self.isMDE else params.storageMDE['creationOptions'],
            'metadataOptions': self.extra_metadata,
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none' if self.tieneCanalAlfa else self.noDataValue
        }

        if(not self.isMDE):
            kwargs['maskBand'] = 4
        else:
            kwargs['xRes'] = 0.2
            kwargs['yRes'] = 0.2

        geotiff = gdal.Translate(gdaloutput, filepath, **kwargs)

        if (params.storage['overviews']):
            self.createOverviews(geotiff)

        if((params.storage['exportJSON']) and (not self.isMDE)):
            self.exportJSONdata(geotiff)

        if(params.storage['previews']):
            self.exportStoragePreview(geotiff)

        return geotiff

    def exportOutline(self, file_ds):
        '''
        Export a vector file with the raster's outline. This file
        must be uploaded to the wms layer in the geoserver
        '''

        def simplificarGeometria(geom):
            return geom.Simplify(params.outlines['simplify'])

        geoDriver = ogr.GetDriverByName("GeoJSON")
        srs = osr.SpatialReference()
        res = srs.ImportFromEPSG(params.geoserver['epsg'])

        if res != 0:
            raise RuntimeError(repr(res) + ': EPSG not found')

        tmpFilename = '{}.geojson'.format(self.outputFilename)

        # Temporary vector file
        tmpGdaloutput = TEMP_FOLDER + "\\" + tmpFilename

        if os.path.exists(tmpGdaloutput):
            geoDriver.DeleteDataSource(tmpGdaloutput)

        tmpOutDatasource = geoDriver.CreateDataSource(tmpGdaloutput)

        outLayer = tmpOutDatasource.CreateLayer("outline", srs=srs)

        maskBand = file_ds.GetRasterBand(4)

        # Create the outline based on the alpha channel
        gdal.Polygonize(maskBand, maskBand, outLayer, -1, [], callback=None)

        tmpOutDatasource = None

        # Final vector file
        gdaloutput = '{}.geojson'.format(self.outputFilename)

        gdaloutput = '{}/{}'.format(
            params.outlines['output_folder'], gdaloutput)

        print('Exporting outline {}'.format(gdaloutput))

        if os.path.exists(gdaloutput):
            geoDriver.DeleteDataSource(gdaloutput)

        outDatasource = geoDriver.CreateDataSource(gdaloutput)

        # create one layer
        layer = outDatasource.CreateLayer(
            "outline", srs=srs, geom_type=ogr.wkbPolygon)

        shp = ogr.Open(tmpGdaloutput, 0)
        tmp_layer = shp.GetLayer()

        biggerGeoms = []

        for feature in tmp_layer:
            geom = feature.geometry()
            area = geom.GetArea()

            # Only keep bigger polygons
            if area > params.outlines['minimum_area']:
                print('Polygon area in m2:', area)
                # Clone to prevent multiiple GDAL bugs
                biggerGeoms.append(geom.Clone())

        tmp_layer = None
        geom = None

        # Convert mutiples Polygons to an unique MultiPolygon
        mergedGeom = ogr.Geometry(ogr.wkbMultiPolygon)

        for geom in biggerGeoms:
            mergedGeom.AddGeometryDirectly(geom)

        # Use this to fix some geometry errors
        mergedGeom = mergedGeom.Buffer(params.outlines['buffer'])

        # https://gdal.org/python/osgeo.ogr.Geometry-class.html#MakeValid
        mergedGeom = mergedGeom.MakeValid()

        if mergedGeom.IsValid() != True:
            print('Invalid geometry')

        else:

            # Simplify the geom to prevent excesive detail and bigger file sizes
            simplifyGeom = simplificarGeometria(mergedGeom)

            if str(simplifyGeom) == 'POLYGON EMPTY':
                print('Error on reading POLYGON')

            else:

                featureDefn = layer.GetLayerDefn()

                featureDefn.AddFieldDefn(ogr.FieldDefn("gsd", ogr.OFTReal))
                featureDefn.AddFieldDefn(ogr.FieldDefn(
                    "registro_id", ogr.OFTInteger64))
                featureDefn.AddFieldDefn(
                    ogr.FieldDefn("map_id", ogr.OFTString))

                if self.date:
                    featureDefn.AddFieldDefn(
                        ogr.FieldDefn("date", ogr.OFTDate))

                # Create the feature and set values
                feature = ogr.Feature(featureDefn)
                feature.SetGeometry(simplifyGeom)

                feature.SetField("gsd", self.original_gsd)
                feature.SetField('map_id', self.mapId)
                feature.SetField('registro_id', self.registroid)

                if self.date:
                    dateFormated = '{}-{}-{}'.format(self.date.strftime(
                        "%Y"), self.date.strftime("%m"), self.date.strftime("%d"))
                    feature.SetField("date", dateFormated)

                layer.CreateFeature(feature)

                feature = None

        outDatasource = None

        # Delete temp files
        del tmpGdaloutput

    def createOverviews(self, ds):
        '''
        Overviews are duplicate versions of your original data, but resampled to a lower resolution
        By default, overviews take the same compression type and transparency masks of the input dataset.

        This allow to speedup opening and viewing the files on QGis, Autocad, Geoserver, etc.
        '''
        ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64, 128, 256])

    def exportJSONdata(self, ds):
        '''
        Export a JSON file
        '''
        outputJSONFilename = '{}.json'.format(self.outputFilename)

        gdaloutput = '{}/{}'.format(
            params.storageJSONdata['output_folder'], outputJSONFilename)

        print('Exporting JSON data {}'.format(gdaloutput))

        # https://gdal.org/python/osgeo.gdal-module.html#InfoOptions

        kwargs = {
            'allMetadata': True,
            'format': 'json'
        }

        data = gdal.Info(ds, **kwargs)

        file = open(gdaloutput, 'w')
        json.dump(data, file)

        file.close()

    def getColorMDE(self, geotiff):
        '''
        Create a color palette to use as a .txt, considering the elevation values
        '''

        array = geotiff.GetRasterBand(1).ReadAsArray()

        srcband = geotiff.GetRasterBand(1)

        # Get raster statistics
        stats = srcband.GetStatistics(True, True)

        # Print the min, max based on stats index
        min = stats[0]
        max = stats[1]

        values = []

        if(min < 0):
            min = min + ((min * - 1) * 0.5)

        trimmedMin = min * 1.31 if max < 60 else min / 1.05

        trimmedMax = max - \
            (max * 0.30) if max < 10 else np.percentile(array, 95)

        per = (trimmedMax-trimmedMin)/7

        cont = 0
        while(cont < 7):
            values.append(trimmedMin)
            trimmedMin += per
            if(cont == 2 or cont == 3 or cont == 5):
                trimmedMin += per
            if(cont == 4):
                trimmedMin += per * 2
            cont += 1

        palette = ["0 0 187 0", "81 222 222 0", "87 237 90 0",
                   "68 236 53 0", "223 227 1 0", "255 134 2 0", "178 0 6 0"]  # bcgyor

        paletteSLD = ["#0000bb", "#51dede", "#57ed5a",
                      "#44ec35", "#dfe301", "#ff8602", "#b20006"]

        palettePath = '{}\\colorPalette.txt'.format(TEMP_FOLDER)

        paletteSLDPath = '{}\\{}.sld'.format(params.output_folder,self.outputFilename)

        fileColor = open(palettePath, 'w')
        fileSLD = open(paletteSLDPath, 'w')

        fileSLD.write('<?xml version="1.0" encoding="UTF-8"?><StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:ogc="http://www.opengis.net/ogc" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" version="1.0.0"><UserLayer><sld:LayerFeatureConstraints><sld:FeatureTypeConstraint/></sld:LayerFeatureConstraints><sld:UserStyle><sld:Name>' +
                      str(geotiff) + '</sld:Name><sld:FeatureTypeStyle><sld:Rule><sld:RasterSymbolizer><sld:ChannelSelection><sld:GrayChannel><sld:SourceChannelName>1</sld:SourceChannelName></sld:GrayChannel></sld:ChannelSelection><sld:ColorMap type="ramp">')

        i = 0
        while i < len(palette):
            # Generating a color palette merging two structures
            mergeColor = str(values[i]) + ' ' + str(palette[i])
            mergeSLD = '<sld:ColorMapEntry color="' + \
                str(paletteSLD[i]) + '"' + ' label="' + str(values[i]) + \
                '" quantity="' + str(values[i]) + '"/>'
            i += 1
            fileColor.write(mergeColor + '\n')
            fileSLD.write(mergeSLD)

        fileSLD.write('</sld:ColorMap></sld:RasterSymbolizer></sld:Rule></sld:FeatureTypeStyle></sld:UserStyle></UserLayer></StyledLayerDescriptor>')

        fileColor.close()
        fileSLD.close()

        return palettePath

    def getColoredHillshade(self, geotiff):
        '''

        Create a colored hillshade result from merging hillshade / DEM
        '''
        tmpColorRelief = '{}\\colorRelief.tif'.format(TEMP_FOLDER)
        tmpHillshade = '{}\\hillshade.tif'.format(TEMP_FOLDER)
        tmpGammaHillshade = '{}\\gammaHillshade.tif'.format(TEMP_FOLDER)
        tmpColoredHillshade = '{}\\coloredHillshade.tif'.format(TEMP_FOLDER)
        tmpColoredHillshadeContrast = '{}\\coloredHillshadeC.tif'.format(TEMP_FOLDER)

        colorPalette = self.getColorMDE(geotiff)

        kwargsColorRelief = {
            'format': params.storageMDEPreview['format'],
            'colorFilename': colorPalette,
            'processing': 'color-relief'
        }

        kwargsHillshade = {
            'format': params.storageMDEPreview['format'],
            'processing': 'hillshade',
            'azimuth': '90',
            'zFactor': '5'
        }

        # Using gdaldem to generate color-Relief and hillshade https://gdal.org/programs/gdaldem.html
        gdal.DEMProcessing(tmpColorRelief, geotiff,
                           **kwargsColorRelief)

        gdal.DEMProcessing(tmpHillshade, geotiff,
                           **kwargsHillshade)

        Calc(["uint8(((A/255)*(0.5))*255)"],
             A=tmpHillshade, outfile=tmpGammaHillshade)
        Calc(["uint8( ( \
                 2 * (A/255.)*(B/255.)*(A<128) + \
                 ( 1 - 2 * (1-(A/255.))*(1-(B/255.)) ) * (A>=128) \
               ) * 255 )"], A=tmpGammaHillshade,
             B=tmpColorRelief, outfile=tmpColoredHillshade, allBands="B")

        im = Image.open(tmpColoredHillshade)
        enhancer = ImageEnhance.Contrast(im)
        factor = 1.12                               # Increase contrast
        im_output = enhancer.enhance(factor)
        im_output.save(tmpColoredHillshadeContrast)

        os.remove(tmpColorRelief)
        os.remove(tmpHillshade)
        os.remove(tmpGammaHillshade)
        os.remove(colorPalette)
        os.remove(tmpColoredHillshade)

        return tmpColoredHillshadeContrast

    def exportStoragePreview(self, geotiff):

        # temporary disable the "auxiliary metadata" because JPG doesn't support it,
        # so this creates an extra file that we don't need (...aux.xml)
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

        outputPreviewFilename = '{}.jpg'.format(self.outputFilename)

        gdaloutput = params.storagePreview['output_folder']
        gdaloutput = '{}/{}'.format(gdaloutput, outputPreviewFilename)

        print('Exporting preview {}'.format(gdaloutput))

        kwargs = {
            'format': params.storagePreview['format'],
            'width': params.storagePreview['width'],  # px
            'creationOptions': params.storagePreview['creationOptions'],
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none'
        }

        if(self.isMDE):
            output = '{}\\lowres.tif'.format(TEMP_FOLDER)
            gdal.Warp(output, geotiff)
            file_ds = gdal.Open(output, gdal.GA_ReadOnly)
            geotiff = self.getColoredHillshade(file_ds)
            file_ds = None

        gdal.Translate(gdaloutput, geotiff,
                       **kwargs)

        if(self.isMDE):
            os.remove(output)
            os.remove(geotiff)

        # reenable the internal metadata
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')


ConvertGeotiff()
