# original tif files
input_folder = 'input'
output_folder = 'output'

output_folder_storage = f'{output_folder}/storage'
output_folder_database = f'{output_folder}/database'
output_folder_geoserver = f'{output_folder}/geoserver'

filename_prefix = '_MapId-'
filename_suffix = '_mde'
outline_suffix = '_outline'
gdalinfo_suffix = '_gdalinfo'
preview_suffix = '_preview'

# To clean the output folder before starting
clean_output_folder = True

no_data = -10000

# https://gdal.org/drivers/raster/gtiff.html#metadata
metadata = [
    'TIFFTAG_ARTIST=Dirección Provincial de Hidráulica, Provincia de Buenos Aires'
]

geoserver = {
    'epsg': 3857,
    'output_folder': output_folder_geoserver + '/rgb',
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
    'output_folder': output_folder_geoserver + '/mde',
    'gsd': 50,  # cm
    'creationOptions': [
        'BIGTIFF=YES',  # for files larger than 4 GB
        'TFW=NO',
        'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=MINISBLACK',
        'COMPRESS=DEFLATE',
    ]
}

storage = {
    'gsd': None,  # None to use original | cm
    'overviews': True,
    'exportJSON': True,  # To export a JSON data file
    'previews': True,
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=YES',
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
        'TILED=NO',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=MINISBLACK',
        'COMPRESS=DEFLATE',
    ]
}


storagePreview = {
    'width': 650,  # px
    # https://gdal.org/drivers/raster/jpeg.html
    'format': 'JPEG',
    'creationOptions': [
        'PROGRESSIVE=ON',  # better for web
        'QUALITY=75',
    ]
}

styleMDE = {
    
    # Remove negative values from mde from the style calculations. Otherwhise, removes only the noData values.
    # This can be used if the mde has some processing errors/holes
    'disregard_values_less_than_0': True,

    # similar to "Cumulative cut count" (Qgis)
    'min_percentile': 0.5,
    'max_percentile': 96,

    'export_quantities': True,

    # min to max
    'palette': [
        "#0000bb",
        "#51dede",
        "#57ed5a",
        "#44ec35",
        "#dfe301",
        "#ff8602",
        "#b20006"
    ]
}

outlines = {
    'enabled': True,

    # Polygons bigger than this area are preserved in the outlines
    'minimum_area': 10,  # m2

    # Use to simplify the geometry
    # https://gdal.org/python/osgeo.ogr.Geometry-class.html#Simplify
    'simplify': 1,

    # Use to fix some geometry errors on the vector
    # https://gdal.org/python/osgeo.ogr.Geometry-class.html#Buffer
    'buffer': 0
}
