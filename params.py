# original tif files
input_folder = 'input'

# https://gdal.org/drivers/raster/gtiff.html#metadata
metadata = [
    'TIFFTAG_ARTIST=Dirección Provincial de Hidráulica, Provincia de Buenos Aires'
]


geoserver = {
    'epsg': 3857,
    'output_folder': 'output/geoserver',
    'gsd': 20,  # cm
    'overviews': True,
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=IF_NEEDED',  # for files larger than 4 GB
        'TFW=NO',
        'TILED=YES',  # forces the creation of a tiled output GeoTiff with default parameters
        'PHOTOMETRIC=YCBCR',  # switches the photometric interpretation to the yCbCr color space, which allows a significant further reduction in output size with minimal changes on the images
        'COMPRESS=JPEG',
        #'PROFILE=GeoTIFF' # Only GeoTIFF tags will be added to the baseline
    ]
}

storage = {
    'output_folder': 'output/storage',
    'gsd': None,  # None to use original | cm
    'overviews': False,
    'creationOptions': [
        'JPEG_QUALITY=80',
        'BIGTIFF=IF_NEEDED',
        'TFW=YES',
        'TILED=YES',
        'PHOTOMETRIC=YCBCR',
        'COMPRESS=JPEG'
    ]
}

storagePreview = {
    'output_folder': 'output/storage/previews',
    'width': 600, #px
    'creationOptions': [
        'JPEG_QUALITY=60',
        'TFW=NO',
        'TILED=NO',
        'PHOTOMETRIC=YCBCR',
        'COMPRESS=JPEG'
    ]
}
