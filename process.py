import sys
import os
import shutil
from pathlib import Path
import math

import params as params
import helpers as h
import generateVRT as vrt

from export_formats.storageRGB import exportStorageRGB
from export_formats.storageDEM import exportStorageDEM
from export_formats.geoserverDEM import exportGeoserverDEM
from export_formats.geoserverRGB import exportGeoserverRGB
from export_formats.previews import exportStoragePreview
from export_formats.quantities import exportQuantities

from version import __version__

try:
    from osgeo import gdal, osr, ogr
except:
    sys.exit('ERROR: osgeo module was not found')


class ConvertGeotiff:
    '''
    Some helpful docs:
    https://pcjericks.github.io/py-gdalogr-cookbook/
    https://docs.geoserver.geo-solutions.it/edu/en/raster_data/advanced_gdal/example5.html
    https://gdal.org/tutorials/raster_api_tut.html
    https://gdal.org/python/osgeo.gdal-module.html
    https://gdal.org/api/python.html

    '''

    def __init__(self):
        print(f'SCRIPT Version: {__version__}')

        version_num = int(gdal.VersionInfo('VERSION_NUM'))
        print(f'GDAL Version: {version_num}')

        print('OPERATION STARTED')

        # Allows GDAL to throw Python Exceptions
        gdal.UseExceptions()

        gdal.SetConfigOption('GDAL_TIFF_INTERNAL_MASK', 'YES')

        self.checkDirectories()
        self.processTifs()
        self.clenTempFolder()

        print('OPERATION FINISHED')

    def checkDirectories(self):
        '''
        Create output folders and remove older files
        '''

        if params.clean_output_folder:
            if os.path.exists(params.output_folder):
                print('-> Removing older files')
                shutil.rmtree(Path(params.output_folder))

        print('-> Creating folders')

        h.createFolder(params.tmp_folder)

        h.createFolder(params.output_folder_database)

        h.createFolder(params.output_folder_database_jsondata)

        h.createFolder(params.output_folder_database_mdevalues)
    
        h.createFolder(params.output_folder_database_outlines)

        h.createFolder(params.output_folder_storage)

        # geoserver folders
        h.createFolder(params.geoserverRGB['output_folder'])
        h.createFolder(params.geoserverDEM['output_folder'])
        h.createFolder(params.geoserverDEMRGB['output_folder'])

    def processTifs(self):

        processed = {}

        # Find files in the input folder
        for subdir, dirs, files in os.walk(params.input_folder):
            for file in files:
                filepath = subdir + os.sep + file
                is_subdir = subdir != params.input_folder
                if ((file.endswith(".tif") | file.endswith(".tiff") | file.endswith(".vrt")) and (not is_subdir)):
                    try:

                        print(f'--> PROCESSING FILE {file} <--')

                        file_ds = gdal.Open(filepath, gdal.GA_ReadOnly)
                        # Number of bands
                        bands = file_ds.RasterCount
                        self.isDEM = bands <= 2

                        lastBand = file_ds.GetRasterBand(bands)
                        self.hasAlphaChannel = (
                            lastBand.GetColorInterpretation() == 6)  # https://github.com/rasterio/rasterio/issues/100
                        self.noDataValue = lastBand.GetNoDataValue()  # take any band

                        # Pix4DMatic injects an erroneous 'nan' value as noData attribute
                        if ((self.noDataValue != None) and (math.isnan(self.noDataValue))):
                            self.noDataValue = 0

                        filenameHasMapId = params.filename_prefix in file

                        if (self.isDEM):

                            print(f'-> File {file} is DEM type')

                            # Generating output filename for DME case
                            self.mapId = h.removeExtension(file.split(
                                params.filename_prefix)[1].split(params.dem_suffix)[0]) if filenameHasMapId else h.createMapId()

                            h.checkFileProcessed(
                                self, filenameHasMapId, True, processed, file)

                            self.registroid = file.split(
                                params.filename_prefix)[0] if filenameHasMapId else h.cleanFilename(h.removeExtension(file.split(params.dem_suffix)[0]))
                        else:

                            print(f'-> File {file} is RGB type')

                            self.mapId = h.removeExtension(
                                file.split(params.filename_prefix)[1]) if filenameHasMapId else h.createMapId()

                            h.checkFileProcessed(
                                self, filenameHasMapId, False, processed, file)

                            self.registroid = file.split(
                                "_")[0] if filenameHasMapId else h.cleanFilename(h.removeExtension(file))

                        output = f'{self.registroid}{params.filename_prefix}{self.mapId}'

                        # Create parent folder for mapId
                        self.outputFolder = f'{params.output_folder_storage}/{output}'
                        h.createFolder(self.outputFolder)

                        self.outputFilename = output if not self.isDEM else '{}{}'.format(
                            output, params.dem_suffix)

                        print(
                            f'-> Files for {self.outputFilename} will be exported')

                        # File GSD
                        gt = file_ds.GetGeoTransform()
                        self.pixelSizeX = gt[1]
                        self.pixelSizeY = -gt[5]

                        # file's GSD: get average x and y values
                        self.originalGsd = round(
                            (self.pixelSizeY + self.pixelSizeX) / 2 * 100, 2)  # cm

                        # File Projection
                        self.epsg = h.getEPSGCode(file_ds)

                        self.date = h.getDateFromMetadata(file_ds)

                        self.extra_metadata = params.metadata

                        self.extra_metadata.append(
                            'registroId={}'.format(self.registroid))

                        self.extra_metadata.append(
                            'mapId={}'.format(self.mapId))

                        self.exportStorageFiles(file_ds)

                        self.exportGeoserverFiles(file_ds, file)

                        # Once we're done, close properly the dataset
                        file_ds = None

                    except RuntimeError as e:
                        print(f'ERROR: Unable to process {filepath}')
                        print(e)
                        sys.exit(1)

    def exportStorageFiles(self, file_ds):
        '''
        Export high and low res files
        '''

        print('EXPORTING STORAGE FILES')

        # creates and low res for some fast operations
        compressedGeotiff = h.getLightVersion(file_ds)

        if (self.isDEM):
            if params.storageDEM['enabled']:
                self.colorValues = h.calculateDEMColorValues(
                    self, compressedGeotiff)

                exportStorageDEM(self, file_ds)

                if params.storageDEM['quantities']:
                    exportQuantities(self)

        else:
            if params.storageRGB['enabled']:
                exportStorageRGB(self, file_ds)

        if (params.previews['enabled']):
            exportStoragePreview(self, compressedGeotiff)

        compressedGeotiff = None

    def exportGeoserverFiles(self, file_ds, file):

        print('EXPORTING GEOSERVER FILES')

        if (self.isDEM):
            if (params.geoserverDEM['enabled'] or params.geoserverDEMRGB['enabled']):
                exportGeoserverDEM(self, file_ds, file)
        else:
            if (params.geoserverRGB['enabled']):
                exportGeoserverRGB(self, file_ds, file)

    def clenTempFolder(self):
        if os.path.exists(params.tmp_folder):
            print('-> Removing temp folder')
            shutil.rmtree(params.tmp_folder)

if(os.listdir(params.input_folder)):
    vrt.generateVRT()
ConvertGeotiff()
