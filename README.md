# Procesamiento de archivos Geotiff
Script en Python para procesar ortomosaicos/geotifs para poderlos subir al geoserver y a la nube apra luego ser descargados.

El script crea los siguientes archivos optimizados:
- para subir al geoserver
    - .tif en calidad intermedia (con overviews en diferentes escalas)
    - .geojson con el contorno de la imagen para subir al wms, con los campos gsd, srs, registroid y date (si existe)
- para subir a la nube:
    - .tif en calidad baja para usar como preview (GSD 80cm)
    - .tif en calidad media/alta para ser alojado en la nube
    - .tfw con la información geoespacial

## Uso
- Colocar archivos .tif a convertir en la carpeta input
- De ser necesario, modificar archivo `params.py` según formatos de exportación, metadata y carpetas.
- Ejecutar `python process.py` para iniciar conversión
