# Procesamiento de archivos Geotiff

Script en Python para procesar ortomosaicos/geotifs para subirlos a geoservers como capa raster, y a la nube para ser descargados.

El script crea los siguientes archivos optimizados:

- para subir al geoserver
  - .tif en calidad intermedia (con overviews/render piramidal en diferentes escalas), EPSG:3857
  - .geojson con el contorno de la imagen para subir al wms, con los campos gsd, srs, registroid y date (si existe)
- para subir a la nube:
  - .tif en calidad baja para usar como preview (w:650px), EPSG original
  - .tif en calidad media/alta para ser alojado en la nube, EPSG original
  - .tfw con la información geoespacial

## Instalación

- Descargar e instalar [Python](https://www.python.org/downloads/)
- Testear en console `python --version` y `pip --version` para corroborar que esté todo andando.
- Descargar [GDAL](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal), seleccionando la versión más nueva de GDAL, y la adecuada según la versión de Python instalado y el procesador. Instalar usando `pip install GDAL-3.3.1-cp37-cp37m-win_amd64.whl` (ajustando según la versión descargada).
- Descargar [Rasterio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio), seleccionando versión análoga al GDAL, e instalar del mismo modo.
- Para poder usar el paquete instalado desde la consola, configurar variables de entorno (poniendo la ruta completa según donde esté instalado el paquete):
  - `GDAL_DATA`: '...\Python\Python37\Lib\site-packages\osgeo\data\gdal'
  - `PROJ_LIB`: '...\Python\Python37\Lib\site-packages\osgeo\data\proj'
  - Agregar a la variable `Path` la ruta '...\Python\Python37\Lib\site-packages\osgeo'
  - Chequear en consola `gdalinfo --version`.
- Instalar la librería Numpy mediante el comando `pip install numpy`.
- Instalar la librería PIL mediante el comando `pip install pillow`.

## Uso

- Colocar los ortomosaicos .tif/.tiff en máxima resolución disponible en la carpeta `input`.
- Ponerles como nombre el número de registro audiovisual al que pertenecen (este dato será incorporado como metadata en los archivos procesados). NOTA: en caso de que un registro tenga más de un mapeo, agregarle al final de cada nombre de archivo un guión y el número; `-1`,`-2`, etc.
- Si se desea procesar un archivo geotiff MDE (Modelo Digital de Elevación), ingresar a continuación del número de registro audiovisual el número de MapId al que pertenece y el sufijo `_mde`, quedando una estructura análoga a `12345678_MapId-123445_mde.tif`.
- En caso de volver a procesar un mismo ortomosaico, debe ingresar como nombre del archivo, el obtenido del procesamiento original.
- Ejecutar `python process.py` para iniciar la conversión. Los archivos procesados serán creados en la carpeta `output`.

## Configuración

- De ser necesario modificar archivo `params.py` según formatos de exportación, metadata y carpetas.

## Combinación de múltiples tiles/mapeos en un solo VRT

- Separar por carpetas el agrupamiento de imágenes deseado.
- Colocar las carpetas generadas en la carpeta `input`, respetando el nombre de cada una de ellas de acuerdo el número de registro.
- En caso de haber una carpeta correspondiente a un ortomosaico MDE, aclararlo durante el nombramiento de dicha carpeta. Por ejemplo, si el número de registro de la versión MDE es `123456`, establecer como nombre de carpeta `123456_mde`.

## TODO

- Subir automáticamente los archivos storage a la red
- Escribir directamente en base de datos lo que se guarda en la carpeta _database_
- Dividir archivo process.py en diferentes módulos
