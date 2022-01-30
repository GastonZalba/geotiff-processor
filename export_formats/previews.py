import os
from osgeo import gdal
from PIL import Image, ImageEnhance, ImageColor
from osgeo_utils.gdal_calc import Calc

import params as params

TEMP_FOLDER = params.tmp_folder


def exportStoragePreview(self, geotiff):

    # temporary disable the "auxiliary metadata" because JPG doesn't support it,
    # so this creates an extra file that we don't need (...aux.xml)
    gdal.SetConfigOption('GDAL_PAM_ENABLED', 'NO')

    outputPreviewFilename = f'{self.outputFilename}{params.preview_suffix}.jpg'

    gdaloutput = '{}/{}'.format(self.outputFolder, outputPreviewFilename)

    print(f'-> Exporting preview {gdaloutput}')

    if (self.isDEM):
        geotiff = getColoredHillshade(self, geotiff)

    gdal.Translate(
        gdaloutput,
        geotiff,
        **{
            # https://gdal.org/drivers/raster/jpeg.html
            'format': 'JPEG',
            'width': params.previews['width'],  # px
            'creationOptions': [
                'PROGRESSIVE=ON', # better for web
                'QUALITY=75',
            ],
            # to fix old error in Drone Deploy exports (https://gdal.org/programs/gdal_translate.html#cmdoption-gdal_translate-a_nodata)
            'noData': 'none'
        }
    )

    if (self.isDEM):
        os.remove(geotiff)

    # reenable the internal metadata
    gdal.SetConfigOption('GDAL_PAM_ENABLED', 'YES')


def getColoredHillshade(self, geotiff):
    '''
    Create a colored hillshade result from merging hillshade / DEM
    '''
    tmpColorRelief = '{}\\colorRelief.tif'.format(TEMP_FOLDER)
    tmpHillshade = '{}\\hillshade.tif'.format(TEMP_FOLDER)
    tmpGammaHillshade = '{}\\gammaHillshade.tif'.format(TEMP_FOLDER)
    tmpColoredHillshade = '{}\\coloredHillshade.tif'.format(TEMP_FOLDER)
    tmpColoredHillshadeContrast = '{}\\coloredHillshadeC.tif'.format(
        TEMP_FOLDER)
    tmpFileColorPath = '{}\\colorPalette.txt'.format(TEMP_FOLDER)

    fileColor = open(tmpFileColorPath, 'w')

    rgbPalette = [' '.join(map(str, ImageColor.getcolor(x, 'RGB')))
                  for x in params.styleDEM['palette']]

    # Write palette file to be imported in gdal
    i = 0
    while i < len(params.styleDEM['palette']):
        # Generating a color palette merging two structures
        mergeColor = str(self.colorValues[i]) + ' ' + \
            str(rgbPalette[i])
        fileColor.write(mergeColor + '\n')
        i += 1

    fileColor.close()

    # Using gdaldem to generate color-Relief and hillshade https://gdal.org/programs/gdaldem.html
    gdal.DEMProcessing(
        tmpColorRelief,
        geotiff,
        **{
            'format': 'JPEG',
            'colorFilename': tmpFileColorPath,
            'processing': 'color-relief'
        }
    )

    gdal.DEMProcessing(
        tmpHillshade,
        geotiff,
        **{
            'format': 'JPEG',
            'processing': 'hillshade',
            'azimuth': '90',
            'zFactor': '5'
        }
    )

    # Adjust hillshade gamma values
    Calc(["uint8(((A/255)*(0.5))*255)"],
         A=tmpHillshade,
         outfile=tmpGammaHillshade,
         overwrite=True
         )

    # Merge hillshade and color
    Calc(["uint8( ( \
                2 * (A/255.)*(B/255.)*(A<128) + \
                ( 1 - 2 * (1-(A/255.))*(1-(B/255.)) ) * (A>=128) \
            ) * 255 )"],
         A=tmpGammaHillshade,
         B=tmpColorRelief,
         outfile=tmpColoredHillshade,
         allBands="B",
         overwrite=True
         )

    im = Image.open(tmpColoredHillshade)
    enhancer = ImageEnhance.Contrast(im)
    factor = 1.12  # Increase contrast
    im_output = enhancer.enhance(factor)
    im_output.save(tmpColoredHillshadeContrast)

    os.remove(tmpColorRelief)
    os.remove(tmpHillshade)
    os.remove(tmpGammaHillshade)
    os.remove(tmpFileColorPath)
    os.remove(tmpColoredHillshade)

    return tmpColoredHillshadeContrast
