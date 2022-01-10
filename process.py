import sys
import os
import shutil
import json
import math
import tempfile
import numpy as np
from pathlib import Path
from osgeo_utils.gdal_calc import Calc
from PIL import Image, ImageEnhance, ImageColor

import params as params
import helpers as h

from version import __version__

try:
    from osgeo import gdal, osr, ogr
except:
    sys.exit('ERROR: osgeo module was not found')

TEMP_FOLDER = tempfile.gettempdir()


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

        h.createFolder(params.output_folder_database)

        h.createFolder(params.output_folder_storage)

        # geoserver folders
        h.createFolder(params.geoserver['output_folder'])
        h.createFolder(params.geoserverMDE['output_folder'])

    def processTifs(self):

        # Find all .tif extensions in the inout folder
        for subdir, dirs, files in os.walk(params.input_folder):
            for file in files:
                filepath = subdir + os.sep + file

                if (file.endswith(".tif") | file.endswith(".tiff")):
                    try:
                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                    except RuntimeError as e:
                        print(f'Unable to open {filepath}')
                        print(e)
                        sys.exit(1)

                # Number of bands
                bandas = file_ds.RasterCount
                self.isMDE = bandas <= 2

                ultimaBanda = file_ds.GetRasterBand(bandas)
                self.tieneCanalAlfa = (
                    ultimaBanda.GetColorInterpretation() == 6)  # https://github.com/rasterio/rasterio/issues/100
                self.noDataValue = ultimaBanda.GetNoDataValue()  # take any band

                # Pix4DMatic injects an erroneous 'nan' value as noData attribute
                if (math.isnan(self.noDataValue)):
                    self.noDataValue = 0

                filenameHasMapId = params.filename_prefix in file

                if (self.isMDE):
                    # Generating output filename for DME case
                    self.mapId = h.removeExtension(file.split(
                        params.filename_prefix)[1].split(params.filename_suffix)[0]) if filenameHasMapId else h.createMapId()

                    self.registroid = file.split(
                        params.filename_prefix)[0] if filenameHasMapId else h.cleanFilename(h.removeExtension(file.split(params.filename_suffix)[0]))
                else:
                    self.mapId = h.removeExtension(
                        file.split(params.filename_prefix)[1]) if filenameHasMapId else h.createMapId()

                    self.registroid = file.split(
                        "_")[0] if filenameHasMapId else h.cleanFilename(h.removeExtension(file))

                output = f'{self.registroid}{params.filename_prefix}{self.mapId}'

                # Create parent folder for mapId
                self.outputFolder = f'{params.output_folder_storage}/{output}'
                h.createFolder(self.outputFolder)

                self.outputFilename = output if not self.isMDE else '{}{}'.format(
                    output, params.filename_suffix)

                # File GSD
                gt = file_ds.GetGeoTransform()
                self.pixelSizeX = gt[1]
                self.pixelSizeY = -gt[5]

                # file's GSD: get average x and y values
                self.originalGsd = round(
                    (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

                # File Projection
                self.epsg = h.getEPSGCode(file_ds)

                self.date = h.getDateFromMetadata(file_ds)

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

    def exportGeoserverFiles(self, file_ds, file):

        print(f'Converting {file}...')

        tmpWarp = None

        warp = False

        kwargs = {
            'format': 'GTiff',
            'xRes': params.geoserver['gsd']/100,
            'yRes': params.geoserver['gsd']/100,
            'multithread': True,
            # force 'none' to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'srcNodata': 'none' if self.tieneCanalAlfa else self.noDataValue
        }

        # change all tiff noData values to the same value
        if (kwargs['srcNodata'] != params.no_data and kwargs['srcNodata'] != 'none'):
            kwargs['dstNodata'] = params.no_data
            warp = True
            print(
                f'Changing noData value from {self.noDataValue} to {params.no_data}')

        # if file has diferent epsg, convert
        if (self.epsg != params.geoserver['epsg']):
            kwargs['srcSRS'] = 'EPSG:{}'.format(self.epsg)
            kwargs['dstSRS'] = 'EPSG:{}'.format(params.geoserver['epsg'])
            warp = True
            print(
                f'Converting EPSG:{self.epsg} to EPSG:{params.geoserver["epsg"]}')

        if (warp):
            tmpWarp = TEMP_FOLDER + "\\" + file
            file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

        outputFilename = f'{self.outputFilename}.tif'

        gdaloutput = params.geoserver['output_folder'] if not self.isMDE else params.geoserverMDE['output_folder']
        gdaloutput = f'{gdaloutput}/{outputFilename}'

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3] if not self.isMDE else [1],
            'xRes': params.geoserver['gsd']/100 if not self.isMDE else params.geoserverMDE['gsd']/100,
            'yRes': params.geoserver['gsd']/100 if not self.isMDE else params.geoserverMDE['gsd']/100,
            'creationOptions': params.geoserver['creationOptions'] if not self.isMDE else params.geoserverMDE['creationOptions'],
            'metadataOptions': self.extra_metadata,
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none' if self.tieneCanalAlfa else params.no_data
        }

        if (not self.isMDE):
            kwargs['maskBand'] = 4

        file_ds = gdal.Translate(gdaloutput, file_ds, **kwargs)

        if (params.outlines['enabled'] and not self.isMDE):
            self.exportOutline(file_ds)

        if (params.geoserver['overviews']):
            self.createOverviews(file_ds)

        file_ds = None

        # Delete tmp files
        if warp:
            del tmpWarp

    def exportStorageFiles(self, file_ds):
        '''
        Export high and low res files
        '''

        outputFilename = '{}.tif'.format(self.outputFilename)

        gdaloutput = self.outputFolder

        gdaloutput = '{}/{}'.format(gdaloutput, outputFilename)

        print(f'Exporting {gdaloutput}')

        tmpWarp = None

        warp = False

        kwargs = {
            'format': 'GTiff',
            'xRes': params.geoserver['gsd']/100,
            'yRes': params.geoserver['gsd']/100,
            'multithread': True,
            # force 'none' to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'srcNodata': 'none' if self.tieneCanalAlfa else self.noDataValue
        }

        # change all tiff noData values to the same value
        if (kwargs['srcNodata'] != params.no_data and kwargs['srcNodata'] != 'none'):
            kwargs['dstNodata'] = params.no_data
            warp = True
            print(
                f'Changing noData value from {self.noDataValue} to {params.no_data}')

        if (warp):
            tmpWarp = f'{TEMP_FOLDER}\\file_ds'
            file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3] if not self.isMDE else [1],
            'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
            'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
            'creationOptions': params.storage['creationOptions'] if not self.isMDE else params.storageMDE['creationOptions'],
            'metadataOptions': self.extra_metadata,
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none' if self.tieneCanalAlfa else params.no_data
        }

        if (not self.isMDE):
            kwargs['maskBand'] = 4
        else:
            kwargs['xRes'] = params.storageMDE['gsd']/100
            kwargs['yRes'] = params.storageMDE['gsd']/100

        geotiff = gdal.Translate(gdaloutput, file_ds, **kwargs)

        if (params.storage['overviews']):
            self.createOverviews(geotiff)

        if ((params.storage['exportJSON'])):
            self.exportJSONdata(geotiff)

        if (params.storage['previews']):
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

        tmpFilename = f'{self.outputFilename}{params.outline_suffix}.geojson'

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
        gdaloutput = f'{params.output_folder_database}/{self.outputFilename}.geojson'

        print(f'Exporting outline {self.outputFilename}')

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

                feature.SetField("gsd", self.originalGsd)
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

        gdaloutput = f'{params.output_folder_database}/{self.outputFilename}{params.gdalinfo_suffix}.json'

        print(f'Exporting JSON data {gdaloutput}')

        # https://gdal.org/python/osgeo.gdal-module.html#InfoOptions

        data = gdal.Info(ds, format='json')

        file = open(gdaloutput, 'w')
        json.dump(data, file)

        file.close()

    def getMdeColorValues(self, geotiff):
        '''
        Create a color palette to use as a .txt, considering the elevation values
        '''

        colorValues = []

        array = np.array(geotiff.GetRasterBand(1).ReadAsArray())

        array = np.array(array.flat)

        # Remove NoDataValue, it doesn't mess up the percentage calculation
        if (params.styleMDE['disregard_values_less_than_0']):
            array = np.ma.masked_less(array, 0, False)
            array = array.compressed()
        else:
            if (self.noDataValue != 'none'):
                array = np.ma.masked_equal(array, self.noDataValue, False)
                array = array.compressed()

        # remove nan values
        array = np.nan_to_num(array)

        # similar to "Cumulative cut count" (Qgis)
        trimmedMin = np.percentile(
            array,
            params.styleMDE['min_percentile']
        )
        print('Trimmed Min:', trimmedMin)

        trimmedMax = np.percentile(
            array,
            params.styleMDE['max_percentile']
        )
        print('Trimmed Max:', trimmedMax)

        if (math.isnan(trimmedMax) or math.isnan(trimmedMin)):
            raise RuntimeError('Reading nan values')

        per = ((trimmedMax / 2) - (trimmedMin / 2)) / 7

        cont = 0
        while(cont < 7):
            colorValues.append(trimmedMin)
            trimmedMin += per
            if (cont == 1):
                trimmedMin += per
            elif (cont == 3):
                trimmedMin += per * 3
            elif (cont == 4 or cont == 5):
                trimmedMin += per * 2
            cont += 1

        return colorValues

    def exportQuantities(self, colorValues):

        quantities = []

        quantitiesPath = '{}\\{}.txt'.format(
            params.output_folder_database, self.outputFilename)

        fileQuantities = open(quantitiesPath, 'w')

        i = 0
        fileQuantities.write('{')
        while i < len(params.styleMDE['palette']):
            # Generating a color palette merging two structures
            quantities.append(str(round(colorValues[i], 6)))
            i += 1
        fileQuantities.write(",".join(quantities))
        fileQuantities.write('}')
        fileQuantities.close()

    def getColoredHillshade(self, geotiff):
        '''

        Create a colored hillshade result from merging hillshade / DEM
        '''
        tmpColorRelief = '{}\\colorRelief.tif'.format(TEMP_FOLDER)
        tmpHillshade = '{}\\hillshade.tif'.format(TEMP_FOLDER)
        tmpGammaHillshade = '{}\\gammaHillshade.tif'.format(TEMP_FOLDER)
        tmpColoredHillshade = '{}\\coloredHillshade.tif'.format(TEMP_FOLDER)
        tmpColoredHillshadeContrast = '{}\\coloredHillshadeC.tif'.format(
            TEMP_FOLDER)
        tmpFileColorPath = '{}\\colorPalette.txt'.format(TEMP_FOLDER)
        tmpGeotiffCompressed = '{}\\mde_compress.tif'.format(TEMP_FOLDER)

        # Warp to make faster processing
        geotiff = gdal.Warp(
            tmpGeotiffCompressed,
            geotiff,
            **{
                'format': 'GTiff',
                'xRes': 0.3,
                'yRes': 0.3
            }
        )

        colorValues = self.getMdeColorValues(geotiff)

        if params.styleMDE['export_sld']:
            self.exportQuantities(colorValues)

        fileColor = open(tmpFileColorPath, 'w')

        rgbPalette = [' '.join(map(str, ImageColor.getcolor(x, 'RGB')))
                      for x in params.styleMDE['palette']]

        # Write palette file to be imported in gdal
        i = 0
        while i < len(params.styleMDE['palette']):
            # Generating a color palette merging two structures
            mergeColor = str(colorValues[i]) + ' ' + \
                str(rgbPalette[i])
            fileColor.write(mergeColor + '\n')
            i += 1

        fileColor.close()

        # Using gdaldem to generate color-Relief and hillshade https://gdal.org/programs/gdaldem.html
        gdal.DEMProcessing(
            tmpColorRelief,
            geotiff,
            **{
                'format': 'JPEG',
                'colorFilename': tmpFileColorPath,
                'processing': 'color-relief'
            }
        )

        gdal.DEMProcessing(
            tmpHillshade,
            geotiff,
            **{
                'format': 'JPEG',
                'processing': 'hillshade',
                'azimuth': '90',
                'zFactor': '5'
            }
        )

        # Adjust hillshade gamma values
        Calc(["uint8(((A/255)*(0.5))*255)"],
             A=tmpHillshade, outfile=tmpGammaHillshade, overwrite=True)

        # Merge hillshade and color
        Calc(["uint8( ( \
                 2 * (A/255.)*(B/255.)*(A<128) + \
                 ( 1 - 2 * (1-(A/255.))*(1-(B/255.)) ) * (A>=128) \
               ) * 255 )"], A=tmpGammaHillshade,
             B=tmpColorRelief, outfile=tmpColoredHillshade, allBands="B", overwrite=True)

        im = Image.open(tmpColoredHillshade)
        enhancer = ImageEnhance.Contrast(im)
        factor = 1.12                               # Increase contrast
        im_output = enhancer.enhance(factor)
        im_output.save(tmpColoredHillshadeContrast)

        os.remove(tmpColorRelief)
        os.remove(tmpHillshade)
        os.remove(tmpGammaHillshade)
        os.remove(tmpFileColorPath)
        os.remove(tmpColoredHillshade)

        return tmpColoredHillshadeContrast

    def exportStoragePreview(self, geotiff):

        # temporary disable the "auxiliary metadata" because JPG doesn't support it,
        # so this creates an extra file that we don't need (...aux.xml)
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

        outputPreviewFilename = f'{self.outputFilename}_preview.jpg'

        gdaloutput = '{}/{}'.format(self.outputFolder, outputPreviewFilename)

        print(f'Exporting preview {gdaloutput}')

        if (self.isMDE):
            geotiff = self.getColoredHillshade(geotiff)

        gdal.Translate(
            gdaloutput,
            geotiff,
            **{
                'format': params.storagePreview['format'],
                'width': params.storagePreview['width'],  # px
                'creationOptions': params.storagePreview['creationOptions'],
                # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
                'noData': 'none'
            }
        )

        if (self.isMDE):
            os.remove(geotiff)

        # reenable the internal metadata
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')


ConvertGeotiff()
