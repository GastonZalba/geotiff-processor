# original tif files
input_folder = 'input'
output_folder = 'output'

filename_prefix = '_MapId-'
filename_suffix = '_mde'


# To clean the output folder before starting
clean_output_folder = True

# https://gdal.org/drivers/raster/gtiff.html#metadata
metadata = [
    'TIFFTAG_ARTIST=Dirección Provincial de Hidráulica, Provincia de Buenos Aires'
]

geoserver = {
    'epsg': 3857,
    'output_folder': output_folder + '/geoserver/rgb',
    'gsd': 20,  # cm
    'overviews': True,
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=IF_NEEDED',  # for files larger than 4 GB
        'TFW=NO',
        'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=YCBCR',  # switches the photometric interpretation to the yCbCr color space, which allows a significant further reduction in output size with minimal changes on the images
        'COMPRESS=JPEG',
        # 'PROFILE=GeoTIFF' # Only GeoTIFF tags will be added to the baseline
    ]
}

geoserverMDE = {
    'output_folder': output_folder + '/geoserver/mde',
    'gsd': 50,  # cm
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=YES',  # for files larger than 4 GB
        'TFW=NO',
        'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=MINISBLACK',
        'COMPRESS=DEFLATE',
    ]
}

storage = {
    'output_folder': output_folder + '/storage',
    'gsd': None,  # None to use original | cm
    'overviews': True,
    'exportJSON': True,  # To export a JSON data file
    'previews': True,
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=IF_NEEDED',
        'TFW=YES',
        'TILED=YES',
        'PHOTOMETRIC=YCBCR',
        'COMPRESS=JPEG',
    ]
}

storageMDE = {
    'gsd': 20,  # cm
    'creationOptions': [
        'BIGTIFF=YES',  # for files larger than 4 GB
        'TFW=YES',
        'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=MINISBLACK',
        'COMPRESS=DEFLATE',
    ]
}

storageJSONdata = {
    'output_folder': output_folder + '/storage/jsondata'
}

storagePreview = {
    'output_folder': output_folder + '/storage/previews',
    'width': 650,  # px
    # https://gdal.org/drivers/raster/jpeg.html
    'format': 'JPEG',
    'creationOptions': [
        'PROGRESSIVE=ON',  # better for web
        'QUALITY=75',
    ]
}

storageMDEPreview = {
    'format': 'JPEG',
    'colorFilename': 'colorPalette.txt'
}

mdeStyle = {
    'disregard_values_than_0': False,    # for blue color
    'min_percentile': 0.5,
    'max_percentile': 96
}

outlines = {
    'enabled': True,
    'output_folder': output_folder + '/storage/outlines',

    # Polygons bigger than this area arepreserved in the outlines
    'minimum_area': 10,  # m2

    # Use to simplify the geometry
    # https://gdal.org/python/osgeo.ogr.Geometry-class.html#Simplify
    'simplify': 1,

    # Use to fix some geometry errors on the vector
    # https://gdal.org/python/osgeo.ogr.Geometry-class.html#Buffer
    'buffer': 0
}
