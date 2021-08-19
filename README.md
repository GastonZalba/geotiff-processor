# Procesamiento de archivos Geotiff
Script en Python para procesar ortomosaicos/geotifs para poder ser subidos a geoservers como capa raster, y a la nube para ser descargados.

El script crea los siguientes archivos optimizados:
- para subir al geoserver
    - .tif en calidad intermedia (con overviews/render piramidal en diferentes escalas)
    - .geojson con el contorno de la imagen para subir al wms, con los campos gsd, srs, registroid y date (si existe)
- para subir a la nube:
    - .tif en calidad baja para usar como preview (GSD 80cm)
    - .tif en calidad media/alta para ser alojado en la nube
    - .tfw con la información geoespacial

## Instalación
- Descargar e instalar [Python](https://www.python.org/downloads/)
- Descargar [GDAL](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal), seleccionando la versión más nueva de GDAL, y la adecuada según la versión de Python instalado y el procesador. Instalar usando `pip install GDAL-3.3.1-cp37-cp37m-win_amd64.whl` (ajustando según la versión descargada).

## Uso
- Colocar los ortomosaicos .tif/.tiff en máxima resolución disponible en la carpeta `input`
- Ponerles como nombre el número de registro audiovisual al que pertenecen (este dato será incorporado como metadata en los archivos procesados)
- Ejecutar `python process.py` para iniciar la conversión. Loa rchivos procesador serán creados en la carpeta `output`

## Configuración
- De ser necesario modificar archivo `params.py` según formatos de exportación, metadata y carpetas.

## TODO
- Subir automáticamente los archivos a la capa vectorials y a la carpeta de red


