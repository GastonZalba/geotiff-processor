import sys
import os

try:
    # https://pcjericks.github.io/py-gdalogr-cookbook/
    # https://docs.geoserver.geo-solutions.it/edu/en/raster_data/advanced_gdal/example5.html
    # https://gdal.org/tutorials/raster_api_tut.html
    # https://gdal.org/python/osgeo.gdal-module.html#WarpOptions
    from osgeo import gdal, osr
except:
    sys.exit('ERROR: no se encontró el módulo GDAL')


INPUT_FOLDER = 'input'
EPSG_OUTPUT = '3857'


class ConvertGeotiff:

    def __init__(self):
        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print('GDAL Version: {}'.format(version_num))

        # this allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')

        self.openFolder()

    def openFolder(self):

        # buscamos todos los archivos con extensión "tif" dentro de la carpeta
        for subdir, dirs, files in os.walk(INPUT_FOLDER):
            for file in files:
                filepath = subdir + os.sep + file

                if filepath.endswith(".tif"):
                    try:
                        file_ds = gdal.Open(filepath)
                    except RuntimeError as e:
                        print('Unable to open {}'.format(filepath))
                        print(e)
                        sys.exit(1)

                    # GSD
                    gt = file_ds.GetGeoTransform()
                    self.pixelSizeX = gt[1]
                    self.pixelSizeY = -gt[5]

                    # Projection
                    prj = file_ds.GetProjection()
                    srs = osr.SpatialReference(wkt=prj)
                    self.epsg = int(srs.GetAttrValue('AUTHORITY', 1))

                    geotiff = self.exportStorageFiles(filepath, file)

                    # usamos el geotiff ya exportado para no volver a abrir el archivo original que e smuy pesado
                    self.exportGeoserverGeotiff(geotiff, file)

                    # Once we're done, close properly the dataset
                    geotiff = None
                    file_ds = None

    def exportGeoserverGeotiff(self, filepath, file):

        GEOSERVER_GSD_OUTPUT = 20  # cm
        COMPRESSION_OUTPUT = 'JPEG'
        OUTPUT_FOLDER = 'output/geoserver'
        QUALITY = 80

        gdaloutput = OUTPUT_FOLDER + '/' + \
            os.path.splitext(
                file)[0] + '_EPSG-{}_GSD-{}.tif'.format(EPSG_OUTPUT, GEOSERVER_GSD_OUTPUT)
        
        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            #'bandList': [1, 2, 3],
            #'maskBand': 4,
            'xRes': GEOSERVER_GSD_OUTPUT/100,
            'yRes': GEOSERVER_GSD_OUTPUT/100,
            'creationOptions': [
                'BIGTIFF=IF_NEEDED',
                'TILED=YES',
                'PHOTOMETRIC=YCBCR',
                'JPEG_QUALITY={}'.format(QUALITY),
                'COMPRESS={}'.format(COMPRESSION_OUTPUT)
            ]
        }
        
        if (self.epsg != 3857):
            print('Converting EPSG:{} to EPSG:{}'.format(self.epsg, EPSG_OUTPUT))
            gdal.Warp(gdaloutput, filepath, dstSRS='EPSG:{}'.format(EPSG_OUTPUT), **kwargs)            
        
        ds = gdal.Translate(gdaloutput, filepath, **kwargs)
        
        self.createOverviews(ds)
        ds = None

     
    def exportStorageFiles(self, filepath, file):

        COMPRESSION_OUTPUT = 'JPEG'
        OUTPUT_FOLDER = 'output/storage'

        # GSD original del archivo: sacamos promedio del valor x e y
        STORAGE_GSD_OUTPUT = round(
            (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

        STORAGE_QUALITY = 80

        gdaloutput = os.path.splitext(
            file)[0] + '_EPSG-{}_GSD-{}.tif'.format(self.epsg, STORAGE_GSD_OUTPUT)

        gdaloutput = OUTPUT_FOLDER + '/' + gdaloutput
        
        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'bandList': [1, 2, 3],
            'maskBand': 4,
            'format': 'GTiff',
            'xRes': self.pixelSizeX,
            'yRes': self.pixelSizeY,
            'creationOptions': [
                'BIGTIFF=IF_NEEDED',  # for files larger than 4 GB
                'TFW=YES',
                'JPEG_QUALITY={}'.format(STORAGE_QUALITY),
                'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
                'PHOTOMETRIC=YCBCR',  # switches the photometric interpretation to the yCbCr color space, which allows a significant further reduction in output size with minimal changes on the images
                'COMPRESS={}'.format(COMPRESSION_OUTPUT)
            ]
        }

        geotiff = gdal.Translate(gdaloutput, filepath, **kwargs)

        PREVIEW_GSD_OUTPUT = 80  # cm
        PREVIEW_QUALITY = 80

        gdaloutput = OUTPUT_FOLDER + '/' + os.path.splitext(file)[0] + '_preview.tif'

        print('Exporting {}'.format(gdaloutput))

        kwargs = {
            'format': 'GTiff',
            'xRes': PREVIEW_GSD_OUTPUT/100,
            'yRes': PREVIEW_GSD_OUTPUT/100,
            'creationOptions': [
                'JPEG_QUALITY={}'.format(PREVIEW_QUALITY),
                'PHOTOMETRIC=YCBCR',  # switches the photometric interpretation to the yCbCr color space, which allows a significant further reduction in output size with minimal changes on the images
                'COMPRESS={}'.format(COMPRESSION_OUTPUT)
            ]
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
