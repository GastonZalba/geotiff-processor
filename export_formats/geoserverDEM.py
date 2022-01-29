from osgeo import gdal
import rasterio
import numpy as np

import helpers as h
import params as params

TEMP_FOLDER = params.tmp_folder

def exportGeoserverDEM(self, file_ds, file):
    ''''
    Exports two geoserver versions:
    - 32 bits float
    - RGB Mapbox color conversion
    '''

    kwargs = {
        'format': 'GTiff',
        'multithread': True,
        'xRes': 0.1,
        'yRes': 0.1,
        # force 'none' to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'srcNodata': 'none' if self.tieneCanalAlfa else self.noDataValue
    }

    # change all tiff noData values to the same value
    if (kwargs['srcNodata'] != params.no_data and kwargs['srcNodata'] != 'none'):
        kwargs['dstNodata'] = params.no_data
        print(f'Changing noData value from {self.noDataValue} to {params.no_data}')

    # if file has diferent epsg, convert
    if (self.epsg != params.geoserver['epsg']):
        kwargs['srcSRS'] = 'EPSG:{}'.format(self.epsg)
        kwargs['dstSRS'] = 'EPSG:{}'.format(params.geoserver['epsg'])
        print(f'Transforming EPSG:{self.epsg} to EPSG:{params.geoserver["epsg"]}')

    tmpWarp = TEMP_FOLDER + "\\" + file
    
    # Use the warp to convert projections, change the GSD and correct the noData values
    file_ds = gdal.Warp(tmpWarp, file_ds, **kwargs)

    outputFilename = f'{self.outputFilename}.tif'

    _exportFloat(self, file_ds, outputFilename)

    _exportRGB(self, tmpWarp, outputFilename)

    # Delete tmp files
    del tmpWarp


def _exportFloat(self, file_ds, outputFilename):

    print('Exporting geoserver DEM in 32 bits Float mode')

    gdaloutputDEM = f'{params.geoserverDEM["output_folder"]}/{outputFilename}'

    kwargs = {
        'format': 'GTiff',
        'bandList': [1],
        'xRes': params.geoserverDEM['gsd']/100,
        'yRes': params.geoserverDEM['gsd']/100,
        'creationOptions': [
            'TFW=NO',
            'TILED=YES',
            'PHOTOMETRIC=MINISBLACK',
            'COMPRESS=DEFLATE',
        ],
        'metadataOptions': self.extra_metadata,
        # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
        'noData': 'none' if self.tieneCanalAlfa else params.no_data
    }

    file_ds = gdal.Translate(gdaloutputDEM, file_ds, **kwargs)

    if (params.geoserver['overviews']):
        h.addOverviews(file_ds)
    
    file_ds = None

    
def _exportRGB(self, tmpFile, outputFilename):

    '''
    Encode grayscale DEM to RGB using Mapbox codification
    https://docs.mapbox.com/data/tilesets/guides/access-elevation-data/
    '''
    print('Exporting geoserver DEM in RGB mode')

    gdaloutputDEMRGB = f'{params.geoserverDEMRGB["output_folder"]}/{outputFilename}'

    with rasterio.open(tmpFile) as src:
        dem = src.read(1)

    shape = dem.shape
    r = np.zeros(shape)
    g = np.zeros(shape)
    b = np.zeros(shape)

    r += np.floor_divide((100000 + dem * 10), 65536)
    g += np.floor_divide((100000 + dem * 10), 256) - r * 256
    b += np.floor(100000 + dem * 10) - r * 65536 - g * 256

    meta = src.meta
    meta['dtype'] = rasterio.uint8
    meta['nodata'] = 0 
    meta['count'] = 3
    meta['driver'] = 'JPEG'

    with rasterio.open(gdaloutputDEMRGB, 'w', **meta) as dst:
        dst.write_band(1, r.astype(rasterio.uint8))
        dst.write_band(2, g.astype(rasterio.uint8))
        dst.write_band(3, b.astype(rasterio.uint8))    