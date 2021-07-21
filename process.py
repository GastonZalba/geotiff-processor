import sys
import os
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
    Some docs:
    https://pcjericks.github.io/py-gdalogr-cookbook/
    https://docs.geoserver.geo-solutions.it/edu/en/raster_data/advanced_gdal/example5.html
    https://gdal.org/tutorials/raster_api_tut.html
    https://gdal.org/python/osgeo.gdal-module.html
    https://gdal.org/api/python.html
    '''

    def __init__(self):
        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print('GDAL Version: {}'.format(version_num))

        # this allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')

        self.checkDirectories()
        self.processTifs()

    def checkDirectories(self):
        '''
        Create folders if no exists
        '''
        Path(params.geoserver['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.storage['output_folder']).mkdir(
            parents=True, exist_ok=True)
        Path(params.storagePreview['output_folder']).mkdir(
            parents=True, exist_ok=True)

    def processTifs(self):

        # Find all .tif extensions
        for subdir, dirs, files in os.walk(params.input_folder):
            for file in files:
                filepath = subdir + os.sep + file

                if filepath.endswith(".tif"):
                    try:
                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                    except RuntimeError as e:
                        print('Unable to open {}'.format(filepath))
                        print(e)
                        sys.exit(1)

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

                    # Drone Deploy date
                    self.date = file_ds.GetMetadataItem("acquisitionStartDate")

                    self.extra_metadata = params.metadata

                    # filename must be an unique identifier
                    self.extra_metadata.append('registroId={}'.format(
                        os.path.splitext(file)[0]))  # Unique Identifier

                    print('Exporting storage files...')
                    self.exportStorageFiles(file_ds, file)

                    print('Exporting geoserver files...')
                    self.exportGeoserverFiles(file_ds, file)

                    # Once we're done, close properly the dataset
                    file_ds = None

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

        gdaloutput = params.geoserver['output_folder'] + '/' + \
            os.path.splitext(
                file)[0] + '_EPSG-{}_GSD-{}.tif'.format(params.geoserver['epsg'], params.geoserver['gsd'])

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

        if (params.geoserver['outline']):
            self.exportOutline(fileToConvert, file)

        ds = gdal.Translate(gdaloutput, fileToConvert, **kwargs)

        if (params.geoserver['overviews']):
            self.createOverviews(ds)

        ds = None

        # Delete tmp files
        if tmpWarp:
            del tmpWarp

    def exportStorageFiles(self, filepath, file):
        '''
        Export high and low res files
        '''

        gdaloutput = os.path.splitext(
            file)[0] + '_EPSG-{}_GSD-{}.tif'.format(self.epsg, self.original_gsd)

        gdaloutput = params.storage['output_folder'] + '/' + gdaloutput

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3],
            'maskBand': 4,
            'format': 'GTiff',
            'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
            'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
            'creationOptions': params.storage['creationOptions'],
            'metadataOptions': self.extra_metadata
        }

        geotiff = gdal.Translate(gdaloutput, filepath, **kwargs)

        if (params.storage['overviews']):
            self.createOverviews(geotiff)

        gdaloutput = params.storagePreview['output_folder'] + '/' + \
            os.path.splitext(file)[0] + '_preview.tif'

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'width': params.storagePreview['width'],  # px
            'creationOptions': params.storagePreview['creationOptions'],
            'metadataOptions': self.extra_metadata
        }

        gdal.Translate(gdaloutput, geotiff, **kwargs)

        return geotiff

    def exportOutline(self, file_ds, file):

        def simplificarGeometria(geom):
            return geom.Simplify(params.geoserver['outlineSimplify'])

        geoDriver = ogr.GetDriverByName("GeoJSON")
        srs = osr.SpatialReference()
        res = srs.ImportFromEPSG(params.geoserver['epsg'])

        if res != 0:
            raise RuntimeError(repr(res) + ': no se pudo importar EPSG')
            
        # Creamos archivo temporario con contorno
        tmpGdaloutput = tempfile.gettempdir() + "\\" + os.path.splitext(
             file)[0] + '.geojson'

        if os.path.exists(tmpGdaloutput):
            geoDriver.DeleteDataSource(tmpGdaloutput)

        tmpOutDatasource = geoDriver.CreateDataSource(tmpGdaloutput)

        outLayer = tmpOutDatasource.CreateLayer("outline", srs=srs)

        maskBand = file_ds.GetRasterBand(4)

        gdal.Polygonize(maskBand, maskBand, outLayer, -1, [], callback=None)
 
        tmpOutDatasource = None

        # Creamos archivo final a partir del temporario
        gdaloutput = os.path.splitext(
            file)[0] + '_outline_EPSG-{}.geojson'.format(params.geoserver['epsg'])

        gdaloutput = params.geoserver['output_folder'] + '/' + gdaloutput
        
        print('Exporting outline {}'.format(gdaloutput))

        if os.path.exists(gdaloutput):
            geoDriver.DeleteDataSource(gdaloutput)

        outDatasource = geoDriver.CreateDataSource(gdaloutput)

        # create one layer
        layer = outDatasource.CreateLayer("outline", srs=srs, geom_type=ogr.wkbPolygon)

        shp = ogr.Open(tmpGdaloutput, 0)
        tmp_layer = shp.GetLayer()
        
        bigger = 0
        biggerGeom = 0

        # Sólo conservamos el polígono más grande
        for feature in tmp_layer:
            geom = feature.geometry()
            area = geom.GetArea()
            if (area > bigger):
                bigger = area
                biggerGeom = geom.Clone() # Clonamos para prevenir extraños bugs
        
        tmp_layer = None
        geom = None
        
        # to fix some geometry errors
        biggerGeom = biggerGeom.Buffer(10)

        if biggerGeom.IsValid() != True:
            print('Invalid geometry')

        else:

            # Simplificamos la geometría para que no tenga tanto detalle y pese menos
            simplifyGeom = simplificarGeometria(biggerGeom)
            
            if str(simplifyGeom) == 'POLYGON EMPTY':
                print('Error on reading POLYGON')
        
            else:

                featureDefn = layer.GetLayerDefn()

                featureDefn.AddFieldDefn(ogr.FieldDefn("gsd", ogr.OFTReal))
                featureDefn.AddFieldDefn(ogr.FieldDefn("registroid", ogr.OFTInteger64))

                if self.date:
                    featureDefn.AddFieldDefn(ogr.FieldDefn("date", ogr.OFTDate))

                # Create the feature and set values
                feature = ogr.Feature(featureDefn)
                feature.SetGeometry(simplifyGeom)

                feature.SetField("gsd", self.original_gsd)
                feature.SetField('registroid', os.path.splitext(file)[0])

                if self.date:
                    date = datetime.strptime(self.date[:-6], "%Y-%m-%dT%H:%M:%S")
                    dateFormated = '{}-{}-{}'.format(date.strftime("%Y"), date.strftime("%m"), date.strftime("%d"))
                    feature.SetField("date", dateFormated)

                layer.CreateFeature(feature)

                feature = None
            
        outDatasource = None

        # Eliminamos geojson temporario
        del tmpGdaloutput

    def createOverviews(self, ds):
        '''
        Overviews are duplicate versions of your original data, but resampled to a lower resolution
        By default, overviews take the same compression type and transparency masks of the input dataset
        '''
        ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64, 128, 256])


ConvertGeotiff()
