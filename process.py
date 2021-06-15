import os
from osgeo import gdal

INPUT_FOLDER = 'input'
EPSG_OUTPUT = '3857'

class ConvertGeotiff:

    def __init__(self):
        self.openFolder()

    def openFolder(self):
        
        # buscamos todos los archivos con extensión "tif" dentro de la carpeta
        for subdir, dirs, files in os.walk(INPUT_FOLDER):
            for file in files:
                filepath = subdir + os.sep + file

                if filepath.endswith(".tif"):
                    geotiff = self.exportStorageFiles(filepath, file)

                    # usamos el geotiff ya exportado para no volver a abrir el archivo original que e smuy pesado
                    self.exportGeoserverGeotiff(geotiff, file)

    def exportGeoserverGeotiff(self, filepath, file):
        PREVIEW_GSD_OUTPUT = 30  # cm
        COMPRESSION_OUTPUT = 'JPEG'
        OUTPUT_FOLDER = 'output/geoserver'
        QUALITY = 80

        gdaloutput = OUTPUT_FOLDER + '/' + \
            os.path.splitext(
                file)[0] + '_EPSG-{}_GSD-{}.tif'.format(EPSG_OUTPUT, PREVIEW_GSD_OUTPUT)

        kwargs = {
            'format': 'GTiff',
            'dstSRS': 'EPSG:' + EPSG_OUTPUT,
            'xRes': PREVIEW_GSD_OUTPUT/100,
            'yRes': PREVIEW_GSD_OUTPUT/100,
            'creationOptions': [
                'TFW=YES',
                'JPEG_QUALITY={}'.format(QUALITY),
                'COMPRESS={}'.format(COMPRESSION_OUTPUT)
            ]
        }

        gdal.Warp(gdaloutput, filepath, **kwargs)

    def exportStorageFiles(self, filepath, file):

        COMPRESSION_OUTPUT = 'JPEG'
        OUTPUT_FOLDER = 'output/storage'

        def processGeotiff(filepath, gdaloutput, epsg, compression, quality, gsd, tfw = 'YES'):

            gdaloutput = OUTPUT_FOLDER + '/' + gdaloutput

            kwargs = {
                'format': 'GTiff',
                'dstSRS': 'EPSG:' + epsg,
                'xRes': gsd/100,
                'yRes': gsd/100,
                'creationOptions': [
                    'TFW={}'.format(tfw),
                    'JPEG_QUALITY={}'.format(quality),
                    'COMPRESS={}'.format(compression)
                ]
            }

            gdal.Warp(gdaloutput, filepath, **kwargs)
            return gdaloutput

        STORAGE_GSD_OUTPUT = 5  # cm
        STORAGE_QUALITY = 80

        gdaloutput = os.path.splitext(
            file)[0] + '_EPSG-{}_GSD-{}.tif'.format(EPSG_OUTPUT, STORAGE_GSD_OUTPUT)

        geotiff = processGeotiff(filepath, gdaloutput, EPSG_OUTPUT,
                COMPRESSION_OUTPUT, STORAGE_QUALITY, STORAGE_GSD_OUTPUT)

        PREVIEW_GSD_OUTPUT = 80  # cm
        PREVIEW_QUALITY = 50

        gdaloutput = os.path.splitext(file)[0] + '_preview.tif'

        processGeotiff(geotiff, gdaloutput, EPSG_OUTPUT, COMPRESSION_OUTPUT,
                PREVIEW_QUALITY, PREVIEW_GSD_OUTPUT, 'NO')
        
        return geotiff

ConvertGeotiff()
