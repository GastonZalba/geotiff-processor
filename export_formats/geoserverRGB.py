from osgeo import gdal

from export_formats.outlines import exportOutline
from helpers import addOverviews
import params as params

TEMP_FOLDER = params.tmp_folder

def exportGeoserverRGB(self, file_ds, file):

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
            f'Transforming EPSG:{self.epsg} to EPSG:{params.geoserver["epsg"]}')

    if (warp):
        tmpWarp = TEMP_FOLDER + "\\" + file
        file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

    if (params.outlines['enabled']):
        exportOutline(self, file_ds)

    outputFilename = f'{self.outputFilename}.tif'

    gdaloutput = f'{params.geoserver["output_folder"]}/{outputFilename}'

    kwargs = {
        'format': 'GTiff',
        'bandList': [1, 2, 3],
        'creationOptions': [
            'JPEG_QUALITY=80',
            'BIGTIFF=IF_NEEDED',  # for files larger than 4 GB
            'TFW=NO',
            'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
            'PHOTOMETRIC=YCBCR',  # switches the photometric interpretation to the yCbCr color space, which allows a significant further reduction in output size with minimal changes on the images
            'COMPRESS=JPEG',
            # 'PROFILE=GeoTIFF' # Only GeoTIFF tags will be added to the baseline
        ],
        'maskBand': 4,
        'xRes': params.geoserver['gsd']/100,
        'yRes': params.geoserver['gsd']/100,
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': 'none' if self.tieneCanalAlfa else params.no_data,
    }

    file_ds = gdal.Translate(gdaloutput, file_ds, **kwargs)

    if (params.geoserver['overviews']):
        addOverviews(file_ds)

    file_ds = None

    # Delete tmp files
    if warp:
        del tmpWarp
