import os
from osgeo import gdal

OUTPUT_FOLDER = 'output'
INPUT_FOLDER = 'input'

COMPRESSION_OUTPUT = 'JPEG'
EPSG_OUTPUT = '3857'
GSD_OUTPUT = 30  # cm

class ConvertGeotiff:

    def __init__(self):
        self.openFolder()

    def openFolder(self):
        for subdir, dirs, files in os.walk(INPUT_FOLDER):
            for file in files:
                filepath = subdir + os.sep + file

                if filepath.endswith(".tif"):
                    self.processGeotiff(filepath, file)

    def processGeotiff(self, filepath, file):

        gdaloutput = OUTPUT_FOLDER + '/' + \
            os.path.splitext(
                file)[0] + '_EPSG-{}_GSD-{}.tif'.format(EPSG_OUTPUT, GSD_OUTPUT)

        kwargs = {
            'format': 'GTiff',
            'dstSRS': 'EPSG:' + EPSG_OUTPUT,
            'xRes': GSD_OUTPUT/100,
            'yRes': GSD_OUTPUT/100,
               'creationOptions': [
                'TFW=YES',
                'COMPRESS={}'.format(COMPRESSION_OUTPUT)
            ]
        }

        gdal.Warp(gdaloutput, filepath, **kwargs)


ConvertGeotiff()
