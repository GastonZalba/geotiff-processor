import os
import secrets
from pathlib import Path
from datetime import datetime
from osgeo import osr

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

def createMapId():
    '''
    Random hash to be used as the map id
    https://docs.python.org/3/library/secrets.html
    '''
    return secrets.token_hex(nbytes=6)