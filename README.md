# Procesamiento de archivos Geotiff

Script en Python para procesar ortomosaicos/geotifs para subirlos a geoservers como capa raster, y a la nube para ser descargados.

El script crea los siguientes archivos optimizados:

- para subir al geoserver
  - .tif en calidad intermedia (con overviews/render piramidal en diferentes escalas), EPSG:3857
  - .geojson con el contorno de la imagen para subir al wms, con los campos gsd, srs, registroid y date (si existe)
- para subir a la nube:
  - .tif en calidad baja para usar como preview (w:650px), EPSG original
  - .tif en calidad alta, ideal para importar desde QGis, EPSG original
  - .tif en calidad media, ideal para usar en AutoCAD o Civil 3D, EPSG original
  - .tfw con la información geoespacial (para usar en AutoCAD, por ejemplo)

## Instalación

- Descargar e instalar [Python](https://www.python.org/downloads/)
- Testear en console `python --version` y `pip --version` para corroborar que esté todo andando.
- Descargar [GDAL](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal), seleccionando la versión más nueva de GDAL, y la adecuada según la versión de Python instalado y el procesador. Si se está usando Python 3.7, por ejemplo, descargar y luego instalar usando `pip install GDAL-3.3.1-cp37-cp37m-win_amd64.whl` (siempre ajustando según la versión descargada).
- Descargar [Rasterio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio), seleccionando versión análoga al GDAL, e instalar del mismo modo.
- Para poder usar el paquete instalado desde la consola, configurar variables de entorno (poniendo la ruta completa según donde esté instalado el paquete y la versión de python):
  - `GDAL_DATA`: '...\Python\Python37\Lib\site-packages\osgeo\data\gdal'
  - `PROJ_LIB`: '...\Python\Python37\Lib\site-packages\osgeo\data\proj'
  - Agregar a la variable `Path` la ruta '...\Python\Python37\Lib\site-packages\osgeo'
  - Chequear en consola `gdalinfo --version`.
- Instalar la librería Numpy mediante el comando `pip install numpy`.
- Instalar la librería PIL mediante el comando `pip install pillow`.

## Uso

- Colocar los ortomosaicos .tif/.tiff en máxima resolución disponible en la carpeta `input`. Si el ortomosaico a procesar está en formato tiles, crear una carpeta contenedora con todas las imágenes correspondientes.
- A los ortomosaicos completos (o la carpeta contenedora en el caso de los tiles) ponerles como nombre el número de registro audiovisual al que pertenecen (este dato será incorporado como metadata en los archivos procesados). NOTA: en caso de que un registro tenga más de un mapeo, agregarle al final de cada nombre de archivo un guión y el número; `-1`,`-2`, etc.
- Si se desea procesar un archivo geotiff MDE (Modelo Digital de Elevación), ingresar a continuación del número de registro audiovisual el sufijo `_mde`, quedando una estructura análoga a `12345678_mde.tif`.
- En caso de volver a procesar un ortomosaico existente, y querer preservar el mismo MapId, debe ingresar como nombre del archivo el obtenido del procesamiento original (y en caso de ser un mde, agregar el sufijo `_mde` al final), quedando similar a `12345678_MapId-123445_mde.tif`.
- Ejecutar `python process.py` para iniciar la conversión. Los archivos procesados serán creados en la carpeta `output`.

## Configuración

- De ser necesario modificar archivo `params.py` según formatos de exportación, metadata y carpetas.


## TODO

- Subir automáticamente los archivos storage a la red
- Escribir directamente en base de datos lo que se guarda en la carpeta _database_
- Dividir archivo process.py en diferentes módulos
