import os
import tempfile
from osgeo import gdal

tmp_folder = f'{tempfile.gettempdir()}/geotiff-processor'


def generateVRT():

    salida = []
    ruta = r'E:\geotiff-processor\input'
    cont = os.listdir(ruta)
    for i in cont:
        finalpath = ruta + os.sep + i
        for path, dirs, files in os.walk(finalpath):

            filepath = tmp_folder + '\\list.txt'

            with open(filepath, "w") as l:
                for file in files:
                    ok = path + os.sep + file
                    l.write(ok + '\n')

            with open(filepath, 'r') as f:
                for linea in f:
                    salida += linea.split()

            output = ruta + os.sep + i + '.vrt'

            ds = gdal.BuildVRT(output, salida)
            ds = None  # ds.FlushCache()

            salida.clear()