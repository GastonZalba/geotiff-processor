import json
from osgeo import gdal

import params as params

def exportGdalinfo(self, ds):
    '''
    Export a JSON file with the gdalinfo data
    '''

    gdaloutput = f'{params.output_folder_database_jsondata}/{self.outputFilename}{params.gdalinfo_suffix}.json'

    print(f'-> Exporting gdalinfo data {gdaloutput}')

    # https://gdal.org/python/osgeo.gdal-module.html#InfoOptions

    data = gdal.Info(ds, format='json')

    file = open(gdaloutput, 'w')
    json.dump(data, file)

    file.close()