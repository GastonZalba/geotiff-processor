from osgeo import gdal

from helpers import addOverviews
import params as params
from export_formats.gdalinfo import exportGdalinfo

TEMP_FOLDER = params.tmp_folder


def exportStorageRGB(self, file_ds):

    output_filename = f'{self.outputFilename}.tif'

    gdaloutput = f'{self.outputFolder}/{output_filename}'

    print(f'-> Exporting {gdaloutput}')

    tmpWarp = None

    warp = False

    kwargs = {
        'format': 'GTiff',
        'xRes': params.storageRGB['gsd']/100 if params.storageRGB['gsd'] else self.pixelSizeX,
        'yRes': params.storageRGB['gsd']/100 if params.storageRGB['gsd'] else self.pixelSizeY,
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
        'bandList': [1, 2, 3],
        'xRes': params.storageRGB['gsd']/100 if params.storageRGB['gsd'] else self.pixelSizeX,
        'yRes': params.storageRGB['gsd']/100 if params.storageRGB['gsd'] else self.pixelSizeY,
        'creationOptions': [
            'JPEG_QUALITY=80',
            'BIGTIFF=NO', # If YES, Civil 3d can't open it.
            'TFW=YES',
            'TILED=YES',
            'PHOTOMETRIC=YCBCR',
            'COMPRESS=JPEG',
        ],
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': 'none' if self.hasAlphaChannel else params.no_data,
        'maskBand': 4
    }

    geotiff = gdal.Translate(gdaloutput, file_ds, **kwargs)
  
    if params.storageRGB['overviews']:
        addOverviews(geotiff)

    if params.storageRGB['gdalinfo']:
        exportGdalinfo(self, geotiff)

    if ((self.pixelSizeX + self.pixelSizeY) / 2) < params.storageRGB['gsd_sm_trigger']:
        
        output_filename_sm = f'{self.outputFilename}_sm.tif'
        gdaloutput_sm = f'{self.outputFolder}/{output_filename_sm}'

        kwargs_sm = {
            **kwargs,
            'xRes': params.storageRGB['gsd_sm'] / 100,
            'yRes': params.storageRGB['gsd_sm'] / 100,
        }

        geotiff_sm = gdal.Translate(gdaloutput_sm, file_ds, **kwargs_sm)

        if params.storageRGB['overviews']:
            addOverviews(geotiff_sm)


    return geotiff
