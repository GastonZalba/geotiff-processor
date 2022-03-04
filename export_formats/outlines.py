import os
from osgeo import gdal, osr, ogr
import params as params

TEMP_FOLDER = params.tmp_folder


def exportOutline(self, file_ds):
    '''
    Export a vector file with the raster's outline. This file
    must be uploaded to the wms layer in the geoserver
    '''

    # Final vector file
    gdaloutput = f'{params.output_folder_database_outlines}/{self.outputFilename}.geojson'
    print(f'-> Exporting outline {gdaloutput}')

    geoDriver = ogr.GetDriverByName("GeoJSON")
    srs = osr.SpatialReference()
    res = srs.ImportFromEPSG(params.geoserver_epsg)

    if res != 0:
        raise RuntimeError(repr(res) + ': EPSG not found')

    tmpFilename = f'{self.outputFilename}{params.outline_suffix}.geojson'

    # Temporary vector file
    tmpGdaloutput = TEMP_FOLDER + "\\" + tmpFilename

    if os.path.exists(tmpGdaloutput):
        geoDriver.DeleteDataSource(tmpGdaloutput)

    tmpOutDatasource = geoDriver.CreateDataSource(tmpGdaloutput)

    outLayer = tmpOutDatasource.CreateLayer("outline", srs=srs)

    maskBand = file_ds.GetRasterBand(4)

    # Create the outline based on the alpha channel
    gdal.Polygonize(maskBand, maskBand, outLayer, -1, [], callback=None)

    tmpOutDatasource = None

    if os.path.exists(gdaloutput):
        geoDriver.DeleteDataSource(gdaloutput)

    outDatasource = geoDriver.CreateDataSource(gdaloutput)

    # create one layer
    layer = outDatasource.CreateLayer(
        "outline", srs=srs, geom_type=ogr.wkbPolygon)

    shp = ogr.Open(tmpGdaloutput, 0)
    tmp_layer = shp.GetLayer()

    biggerGeoms = []

    for feature in tmp_layer:
        geom = feature.geometry()
        area = geom.GetArea()

        # Only keep bigger polygons
        if area > params.geoserverRGB['outlines']['minimum_area']:
            print('--> Polygon area in m2:', area)
            # Clone to prevent multiiple GDAL bugs
            biggerGeoms.append(geom.Clone())

    tmp_layer = None
    geom = None

    # Convert mutiples Polygons to an unique MultiPolygon
    mergedGeom = ogr.Geometry(ogr.wkbMultiPolygon)

    for geom in biggerGeoms:
        mergedGeom.AddGeometryDirectly(geom)

    # Use this to fix some geometry errors
    mergedGeom = mergedGeom.Buffer(params.geoserverRGB['outlines']['buffer'])

    # https://gdal.org/python/osgeo.ogr.Geometry-class.html#MakeValid
    mergedGeom = mergedGeom.MakeValid()

    if mergedGeom.IsValid() != True:
        print('-> ERROR: Invalid geometry')

    else:

        # Simplify the geom to prevent excesive detail and bigger file sizes
        simplifyGeom = simplificarGeometria(mergedGeom)

        if str(simplifyGeom) == 'POLYGON EMPTY':
            print('-> Error on reading POLYGON')

        else:

            featureDefn = layer.GetLayerDefn()

            featureDefn.AddFieldDefn(ogr.FieldDefn("gsd", ogr.OFTReal))
            featureDefn.AddFieldDefn(ogr.FieldDefn(
                "registro_id", ogr.OFTInteger64))
            featureDefn.AddFieldDefn(
                ogr.FieldDefn("map_id", ogr.OFTString))

            if self.date:
                featureDefn.AddFieldDefn(
                    ogr.FieldDefn("date", ogr.OFTDate))

            # Create the feature and set values
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(simplifyGeom)

            feature.SetField("gsd", self.originalGsd)
            feature.SetField('map_id', self.mapId)
            feature.SetField('registro_id', self.registroid)

            if self.date:
                dateFormated = f'{self.date.strftime("%Y")}-{self.date.strftime("%m")}-{self.date.strftime("%d")}'
                feature.SetField("date", dateFormated)

            layer.CreateFeature(feature)

            feature = None

    outDatasource = None


def simplificarGeometria(geom):
    return geom.Simplify(params.geoserverRGB['outlines']['simplify'])
