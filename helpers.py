import os
import secrets
from pathlib import Path
from datetime import datetime
from osgeo import osr
import numpy as np
import math
from osgeo import gdal, osr

import params as params

TEMP_FOLDER = params.tmp_folder


def createFolder(folderPath):
    Path(folderPath).mkdir(
        parents=True,
        exist_ok=True
    )


def removeExtension(filename):
    return os.path.splitext(filename)[0]


def getDateFromMetadata(file_ds):
    '''
    Get Date from tif metadata
    '''
    droneDeployDate = file_ds.GetMetadataItem("acquisitionStartDate")
    pix4DMaticDate = file_ds.GetMetadataItem("TIFFTAG_DATETIME")
    # pix4dMapper doesn't store date info? WTF

    if droneDeployDate:
        return datetime.strptime(droneDeployDate[:-6], "%Y-%m-%dT%H:%M:%S")
    elif pix4DMaticDate:
        return datetime.strptime(pix4DMaticDate, "%Y:%m:%d %H:%M:%S")
    else:
        return None


def getEPSGCode(file_ds):
    prj = file_ds.GetProjection()
    srs = osr.SpatialReference(wkt=prj)
    return int(srs.GetAttrValue('AUTHORITY', 1))


def cleanFilename(filename):
    '''
    Check if the filename has a dash and a version number. This occurs when
    there are multiples maps in one registro.está hecho todo bien
    Returns only the registtroid
    '''
    filename = filename.split('-')[0]

    return filename


def addOverviews(gdal_dataset):
    print('-> Adding overviews')
    '''
    Overviews are duplicate versions of your original data, but resampled to a lower resolution
    By default, overviews take the same compression type and transparency masks of the input dataset.

    This allow to speedup opening and viewing the files on QGis, Autocad, Geoserver, etc.
    '''
    gdal_dataset.BuildOverviews("AVERAGE", params.overviews)


def createMapId():
    '''
    Random hash to be used as the map id
    https://docs.python.org/3/library/secrets.html
    '''
    return secrets.token_hex(nbytes=6)


def calculateDEMColorValues(self, geotiff):
    '''
    Create a color palette to use as a .txt, considering the elevation values
    '''

    colorValues = []

    array = np.array(geotiff.GetRasterBand(1).ReadAsArray())

    array = np.array(array.flat)

    print('-> Evaluating DEM values:')

    # Remove NoDataValue, it doesn't mess up the percentage calculation
    if (params.styleDEM['disregard_values_less_than_0']):
        array = np.ma.masked_less(array, 0, False)
        array = array.compressed()
    else:
        if (self.noDataValue != 'none'):
            array = np.ma.masked_equal(array, self.noDataValue, False)
            array = array.compressed()

    # convert nan values no noData
    array = np.nan_to_num(array, nan=params.no_data)

    # similar to "Cumulative cut count" (Qgis)
    trimmedMin = np.percentile(
        array,
        params.styleDEM['min_percentile']
    )
    print('--> Trimmed Min:', trimmedMin)

    trimmedMax = np.percentile(
        array,
        params.styleDEM['max_percentile']
    )
    print('--> Trimmed Max:', trimmedMax)

    if (math.isnan(trimmedMax) or math.isnan(trimmedMin)):
        raise RuntimeError('Reading nan values')

    per = ((trimmedMax / 2) - (trimmedMin / 2)) / 7

    cont = 0
    while(cont < 7):
        colorValues.append(trimmedMin)
        trimmedMin += per
        if (cont == 1):
            trimmedMin += per
        elif (cont == 3):
            trimmedMin += per * 3
        elif (cont == 4 or cont == 5):
            trimmedMin += per * 2
        cont += 1

    return colorValues


def getLightVersion(file_ds):
    '''
    Creates a lightweight version to be used in some fast operations
    like previews, mde stats, etc.
    '''

    print('-> Generating lightweight version')

    # tmp file
    tmpGeotiffCompressed = '{}\\compressedLowRes.tif'.format(TEMP_FOLDER)

    geotiff = gdal.Warp(
        tmpGeotiffCompressed,
        file_ds,
        **{
            'format': 'GTiff',
            'xRes': 0.3,
            'yRes': 0.3
        }
    )

    return geotiff


def checkFileProcessed(self, filenameHasMapId, isMDE, processed, file):
    '''
    Check if the file has already been processed before to reuse hash,
    instead of generating a new one (process rgb and dem at the same time).
    '''

    if not filenameHasMapId:
        exist = False
        f = file.split(params.dem_suffix)[
            0] if isMDE else removeExtension(file)
        for i in processed:  # dictionary elements
            if(f in i):  
                exist = True
                self.mapId = processed.get(f)  # take existing hash
                break
        if not exist:
            # if it was never processed, I add it to the dict
            processed[f] = self.mapId
