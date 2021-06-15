# Procesamiento de archivos Geotiff
Script en Python para procesar ortomosaicos/geotifs para poderlos subir al geoserver y a la [nube](https://nube.minfra.gba.gob.ar/).

El script crea 5 archivos en 2 carpetas:
- `/geoserver`, para subir al geoserver
    - .tif en calidad intermedia (GSD 30cm) para subir al geoserver
    - .tfw con la información geoespacial
- `/storage`, para subir a la nube:
    - .tif en calidad baja para usar como preview (GSD 80cm)
    - .tif en calidad media/alta (GSD 5cm) para ser alojado en la nube
    - .tfw con la información geoespacial

- Por defecto se utiliza compresión JPEG y EPSG:3857.

## @TODO
- Armar archivo .ini para alojar las configuraciones
- Detectar GSD original del archivo para evitar reescalamientos.
- Revisar warnings
