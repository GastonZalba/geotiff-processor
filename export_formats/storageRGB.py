from osgeo import gdal
import params as params

TEMP_FOLDER = params.tmp_folder

def exportStorageRGB(self, file_ds):

    outputFilename = '{}.tif'.format(self.outputFilename)

    gdaloutput = self.outputFolder

    gdaloutput = '{}/{}'.format(gdaloutput, outputFilename)

    print(f'Exporting {gdaloutput}')

    tmpWarp = None

    warp = False

    kwargs = {
        'format': 'GTiff',
        'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
        'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
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
        'bandList': [1, 2, 3],
        'xRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeX,
        'yRes': params.storage['gsd']/100 if params.storage['gsd'] else self.pixelSizeY,
        'creationOptions': [
            'JPEG_QUALITY=80',
            'BIGTIFF=YES',
            'TFW=YES',
            'TILED=YES',
            'PHOTOMETRIC=YCBCR',
            'COMPRESS=JPEG',
        ],
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': 'none' if self.tieneCanalAlfa else params.no_data,
        'maskBand': 4
    }

    geotiff = gdal.Translate(gdaloutput, file_ds, **kwargs)

    return geotiff
