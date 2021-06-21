import sys
import os
import tempfile
from pathlib import Path

import params as params

try:
    from osgeo import gdal, osr
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
        Path(params.geoserver['output_folder']).mkdir(parents=True, exist_ok=True)
        Path(params.storage['output_folder']).mkdir(parents=True, exist_ok=True)
        Path(params.storagePreview['output_folder']).mkdir(parents=True, exist_ok=True)

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

                    # File Projection
                    prj = file_ds.GetProjection()
                    srs = osr.SpatialReference(wkt=prj)
                    self.epsg = int(srs.GetAttrValue('AUTHORITY', 1))

                    self.metadata = params.metadata

                    # filename must be an unique identifier
                    # self.metadata.append('TIFF_RSID={}'.format(file)) # File Universal Unique Identifier

                    print('Exporting storage files...')
                    self.exportStorageFiles(file_ds, file)

                    print('Exporting geoserver files...')                    
                    # use already processed geotiff
                    self.exportGeoserverFiles(file_ds, file)

                    # Once we're done, close properly the dataset
                    file_ds = None

    def exportGeoserverFiles(self, filepath, file):

        tmpWarp = None

        print('Converting {}...'.format(file))

        kwargs = {
            'format': 'GTiff',
            'xRes': params.geoserver['gsd']/100,
            'yRes': params.geoserver['gsd']/100,
            'dstSRS': 'EPSG:{}'.format(params.geoserver['epsg'])
        }

        # if file has diferent epsg
        if (self.epsg != params.geoserver['epsg']):
            tmpWarp = tempfile.gettempdir() + file[0] + '.tif'
            print('Converting EPSG:{} to EPSG:{}'.format(
                self.epsg, params.geoserver['epsg']))
            # https://gis.stackexchange.com/questions/260502/using-gdalwarp-to-generate-a-binary-mask
            ds = gdal.Warp(tmpWarp, filepath, **kwargs)

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
            'metadataOptions': self.metadata
        }

        fileToConvert = ds if tmpWarp else filepath
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
        # file's GSD: get average x and y values
        storage_gsd = round(
            (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

        gdaloutput = os.path.splitext(
            file)[0] + '_EPSG-{}_GSD-{}.tif'.format(self.epsg, storage_gsd)

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
            'metadataOptions': self.metadata
        }

        geotiff = gdal.Translate(gdaloutput, filepath, **kwargs)

        if (params.storage['overviews']):
            self.createOverviews(geotiff)

        gdaloutput = params.storagePreview['output_folder'] + '/' + \
            os.path.splitext(file)[0] + '_preview.tif'

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'xRes': params.storagePreview['gsd']/100,
            'yRes': params.storagePreview['gsd']/100,
            'creationOptions': params.storagePreview['creationOptions'],
            'metadataOptions': self.metadata
        }

        gdal.Translate(gdaloutput, geotiff, **kwargs)

        return geotiff

    def createOverviews(self, ds):
        '''
        Overviews are duplicate versions of your original data, but resampled to a lower resolution
        By default, overviews take the same compression type and transparency masks of the input dataset
        '''
        ds.BuildOverviews("AVERAGE", [2, 4, 8, 16, 32, 64, 128, 256])


ConvertGeotiff()
