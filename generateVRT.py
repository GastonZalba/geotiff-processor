import os
from osgeo import gdal
import params as params


def generateVRT():

    pathList = []
    root_path = params.input_folder
    cont = os.listdir(root_path)
    for i in cont:
        finalpath = root_path + os.sep + i
        for path, dirs, files in os.walk(finalpath):
            filepath = params.tmp_folder + 'list.txt'
            with open(filepath, "w") as l:
                for file in files:
                    if(file.endswith(".tif")):
                        ok = path + os.sep + file
                        l.write(ok + '\n')

            with open(filepath, 'r') as f:
                for line in f:
                    pathList.append(line.split('\n')[0])

            output = root_path + os.sep + i + '.vrt'
            gdal.BuildVRT(output, pathList)

            pathList.clear()
