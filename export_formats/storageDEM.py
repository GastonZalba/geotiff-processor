from osgeo import gdal

from helpers import addOverviews
import params as params
from export_formats.gdalinfo import exportGdalinfo

TEMP_FOLDER = params.tmp_folder


def exportStorageDEM(self, file_ds):
    '''
    Exports highest resolution version
    '''

    outputFilename = f'{self.outputFilename}.tif'

    gdaloutput = self.outputFolder

    gdaloutput = f'{gdaloutput}/{outputFilename}'

    print(f'-> Exporting {gdaloutput}')

    tmpWarp = None

    warp = False

    kwargs = {
        'format': 'GTiff',
        'xRes': params.storageDEM['gsd']/100 if params.storageDEM['gsd'] else self.pixelSizeX,
        'yRes': params.storageDEM['gsd']/100 if params.storageDEM['gsd'] else self.pixelSizeY,
        'multithread': True,
        # force 'none' to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'srcNodata': 'none' if self.hasAlphaChannel else self.noDataValue
    }

    # change all tiff noData values to the same value
    if (kwargs['srcNodata'] != params.no_data and kwargs['srcNodata'] != 'none'):
        kwargs['dstNodata'] = params.no_data
        warp = True
        print(
            f'-> Changing noData value from {self.noDataValue} to {params.no_data}')

    if (warp):
        tmpWarp = f'{TEMP_FOLDER}\\file_ds'
        file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

    kwargs = {
        'format': 'GTiff',
        'xRes': params.storageDEM['gsd']/100 if params.storageDEM['gsd'] else self.pixelSizeX,
        'yRes': params.storageDEM['gsd']/100 if params.storageDEM['gsd'] else self.pixelSizeY,
        'bandList': [1],
        'creationOptions': [
            'BIGTIFF=NO',  # If YES, Civil 3d can't open it.
            'TFW=NO',
            'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
            'PHOTOMETRIC=MINISBLACK',
            'COMPRESS=DEFLATE',
        ],
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': 'none' if self.hasAlphaChannel else params.no_data
    }

    geotiff = gdal.Translate(gdaloutput, file_ds, **kwargs)

    if params.storageDEM['overviews']:
        addOverviews(geotiff)

    if params.storageDEM['gdalinfo']:
        exportGdalinfo(self, geotiff)

    return geotiff
