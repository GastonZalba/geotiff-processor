from osgeo import gdal

from helpers import addOverviews
import params as params

TEMP_FOLDER = params.tmp_folder

def exportGeoserverRGB(self, file_ds):

    tmpWarp = None

    warp = False

    kwargs = {
        'xRes': params.geoserverRGB['gsd']/100 if self.area > params.geoserverRGB['ha_sm_trigger'] else params.geoserverRGB['gsd_sm']/100,
        'yRes': params.geoserverRGB['gsd']/100 if self.area > params.geoserverRGB['ha_sm_trigger'] else params.geoserverRGB['gsd_sm']/100,
        'multithread': True,
        # force 'none' to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'srcNodata': self.noDataValue if not self.hasAlphaChannel else 'none'
    }

    # change all tiff noData values to the same value
    if (kwargs['srcNodata'] != params.no_data and kwargs['srcNodata'] != 'none'):
        kwargs['dstNodata'] = params.no_data
        warp = True
        print(
            f'-> Changing noData value from {self.noDataValue} to {params.no_data}')

    # if file has diferent epsg, convert
    if (self.epsg != params.geoserver_epsg):
        kwargs['srcSRS'] = f'EPSG:{self.epsg}'
        kwargs['dstSRS'] = f'EPSG:{params.geoserver_epsg}'
        warp = True
        print(
            f'-> Transforming EPSG:{self.epsg} to EPSG:{params.geoserver_epsg}')

    if (warp):
        tmpWarp = TEMP_FOLDER + "\\warpTmp.vrt"
        file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)


    outputFilename = f'{self.outputFilename}.tif'

    gdaloutput = f'{params.geoserverRGB["output_folder"]}/{outputFilename}'
    
    print(f'-> Exporting {gdaloutput}')

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
        'maskBand': 4 if self.hasAlphaChannel else 1,
        'xRes': params.geoserverRGB['gsd']/100 if self.area > params.geoserverRGB['ha_sm_trigger'] else params.geoserverRGB['gsd_sm']/100,
        'yRes': params.geoserverRGB['gsd']/100 if self.area > params.geoserverRGB['ha_sm_trigger'] else params.geoserverRGB['gsd_sm']/100,
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': params.no_data if not self.hasAlphaChannel else 'none'
    }

    file_ds = gdal.Translate(gdaloutput, file_ds, **kwargs)

    if (params.geoserverRGB['overviews']):
        addOverviews(file_ds)

    file_ds = None
