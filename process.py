import sys
import os
import secrets
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

import params as params

try:
    from osgeo import gdal, osr, ogr
except:
    sys.exit('ERROR: osgeo module was not found')


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
        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print('GDAL Version: {}'.format(version_num))

        # Allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')
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
        Path(params.outlines['output_folder']).mkdir(
            parents=True, exist_ok=True)

    def processTifs(self):

        # Find all .tif extensions in the inout folder
        for subdir, dirs, files in os.walk(params.input_folder):
            for file in files:
                filepath = subdir + os.sep + file

                if (filepath.endswith(".tif") | filepath.endswith(".tiff")):
                    try:
                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                    except RuntimeError as e:
                        print('Unable to open {}'.format(filepath))
                        print(e)
                        sys.exit(1)

                    # Random hash to be used as the map id
                    # https://docs.python.org/3/library/secrets.html
                    self.hash = secrets.token_hex(nbytes=6)

                    self.registroid = self.cleanFilename(
                        os.path.splitext(file)[0])

                    self.outputFilename = self.registroid + '_' + params.filename_prefix + self.hash

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

                    self.extra_metadata.append('mapId={}'.format(self.hash))

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
        there are multiples maps in one registro.
        Returns only the registtroid
        '''
        filename.split('-')[0]

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
                'dstSRS': 'EPSG:{}'.format(params.geoserver['epsg'])
            }

            tmpWarp = tempfile.gettempdir() + "\\" + file
            print('Converting EPSG:{} to EPSG:{}'.format(
                self.epsg, params.geoserver['epsg']))
            # https://gis.stackexchange.com/questions/260502/using-gdalwarp-to-generate-a-binary-mask
            ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

        outputFilename = self.outputFilename + '.tif'

        gdaloutput = params.geoserver['output_folder'] + '/' + outputFilename

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3],
            'maskBand': 4,
            'xRes': params.geoserver['gsd']/100,
            'yRes': params.geoserver['gsd']/100,
            'creationOptions': params.geoserver['creationOptions'],
            'metadataOptions': self.extra_metadata
        }

        fileToConvert = ds if tmpWarp else file_ds

        if (params.outlines['enabled']):
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

        outputFilename = self.outputFilename + '.tif'

        gdaloutput = params.storage['output_folder'] + '/' + outputFilename

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3],
            'maskBand': 4,
            'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
            'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
            'creationOptions': params.storage['creationOptions'],
            'metadataOptions': self.extra_metadata
        }

        geotiff = gdal.Translate(gdaloutput, filepath, **kwargs)

        # temporary disable the "auxiliary metadata" beacuse JPG doesn't support it,
        # so this creates an extra file that we don't need (...aux.xml)
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

        if (params.storage['overviews']):
            self.createOverviews(geotiff)

        outputPreviewFilename = self.outputFilename + '.jpg'

        gdaloutput = params.storagePreview['output_folder'] + \
            '/' + outputPreviewFilename

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': params.storagePreview['format'],
            'width': params.storagePreview['width'],  # px
            'creationOptions': params.storagePreview['creationOptions']
        }

        gdal.Translate(gdaloutput, geotiff, **kwargs)

        # reenable the internal metadata
        gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')

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

        tmpFilename = self.outputFilename + '.geojson'

        # Temporary vector file
        tmpGdaloutput = tempfile.gettempdir() + "\\" + tmpFilename

        if os.path.exists(tmpGdaloutput):
            geoDriver.DeleteDataSource(tmpGdaloutput)

        tmpOutDatasource = geoDriver.CreateDataSource(tmpGdaloutput)

        outLayer = tmpOutDatasource.CreateLayer("outline", srs=srs)

        maskBand = file_ds.GetRasterBand(4)

        # Create the outline based on the alpha channel
        gdal.Polygonize(maskBand, maskBand, outLayer, -1, [], callback=None)

        tmpOutDatasource = None

        # Final vector file
        gdaloutput = self.outputFilename + '.geojson'

        gdaloutput = params.outlines['output_folder'] + '/' + gdaloutput

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
                biggerGeoms.append(geom.Clone())  # Clone to prevent multiiple GDAL bugs

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
                feature.SetField('map_id', self.hash)
                feature.SetField('registro_id', self.registroid)

                if self.date:
                    dateFormated = '{}-{}-{}'.format(self.date.strftime(
                        "%Y"), self.date.strftime("%m"), self.date.strftime("%d"))
                    feature.SetField("date", dateFormated)

                layer.CreateFeature(feature)

                feature = None

        outDatasource = None

        # Delete temp file
        del tmpGdaloutput

    def createOverviews(self, ds):
        '''
        Overviews are duplicate versions of your original data, but resampled to a lower resolution
        By default, overviews take the same compression type and transparency masks of the input dataset.

        This allow to speedup opening and viewing the files on QGis, Autocad, Geoserver, etc.
        '''
        ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64, 128, 256])


ConvertGeotiff()
