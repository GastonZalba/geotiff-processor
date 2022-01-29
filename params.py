import tempfile

tmp_folder = tempfile.gettempdir()

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
    'overviews': True
}

geoserverDEM = {
    'output_folder': output_folder_geoserver + '/mde',
    'gsd': 50  # cm
}

geoserverDEMRGB = {
    'output_folder': output_folder_geoserver + '/mde_rgb',
    'gsd': 50  # cm
}

storage = {
    'gsd': None,  # None to use original | cm
    'overviews': True,
    'exportJSON': True,  # To export a JSON data file
    'previews': True,
}

storageDEM = {
    'gsd': 20  # cm
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

styleDEM = {

    # Remove negative values from dem from the style calculations. Otherwhise, removes only the noData values.
    # This can be used if the dem has some processing errors/holes
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
