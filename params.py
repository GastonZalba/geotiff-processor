import tempfile

tmp_folder = f'{tempfile.gettempdir()}/geotiff-processor'
extensions = ['.tif', '.tiff', '.vrt']

input_folder = 'input'
output_folder = 'output'

output_folder_storage = f'{output_folder}/storage'
output_folder_database = f'{output_folder}/database'
output_folder_database_jsondata = f'{output_folder_database}/jsondata'
output_folder_database_mdevalues = f'{output_folder_database}/mdevalues'
output_folder_database_outlines = f'{output_folder_database}/outlines'
output_folder_geoserver = f'{output_folder}/geoserver'

filename_prefix = '_MapId-'
dem_suffix = '_mde'
outline_suffix = '_outline'
gdalinfo_suffix = '_gdalinfo'
preview_suffix = '_preview'

# To clean the output folder before starting
clean_output_folder = True

no_data = -10000

overviews = [2, 4, 8, 16, 32, 64, 128, 256]

geoserver_epsg = 3857

# https://gdal.org/drivers/raster/gtiff.html#metadata
metadata = [
    'TIFFTAG_ARTIST=Dirección Provincial de Hidráulica, Provincia de Buenos Aires'
]

geoserverRGB = {
    'enabled': True,
    'output_folder': output_folder_geoserver + '/rgb',
    'gsd': 20, # cm
    'ha_sm_trigger': 150, # If raster is less than these ha, increase the quality of the geoserver images
    'gsd_sm': 10, # cm
    'overviews': True
}

# outlines are exported only in RGB images
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

geoserverDEM = {
    'enabled': True,
    'output_folder': output_folder_geoserver + '/mde',
    'overviews': True,
    'gsd': 50  # cm
}

geoserverDEMRGB = {
    'enabled': True,
    'output_folder': output_folder_geoserver + '/mde_rgb',
    'overviews': True,
    'encoding': 'terrarium' # mapbox | terrarium
}

storageRGB = {
    'enabled': True,
    'gsd': None,  # None to use original | cm
    'gsd_sm_trigger': 5,  # cm 
    'gsd_sm': 10,  # cm Used if the default gsd is less than gsd_limit
    'overviews': True,
    'gdalinfo': True
}

storageDEM = {
    'enabled': True,
    'gsd': 20,  # cm
    'overviews': True,
    'quantities': True,
    'gdalinfo': True
}

previews = {
    'enabled': True,
    'width': 650  # px
}

styleDEM = {

    # Remove negative values from dem from the style calculations. Otherwhise, removes only the noData values.
    # This can be used if the dem has some processing errors/holes
    'disregard_values_less_than_0': True,

    # similar to "Cumulative cut count" (Qgis)
    'min_percentile': 0.5,
    'max_percentile': 96,

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
