# Nihon 2024 · mapa de fotos

Mapa interactivo de mi viaje a Japón (28 de octubre – 16 de noviembre de 2024): la ruta real en tren, bici y avión, día por día, con un carrete de todas las fotos de cada lugar.

**Ver el mapa:** https://kornofilo.github.io/japan-photo-map/

## Cómo está hecho

- `index.html`: una sola página con [Leaflet](https://leafletjs.com/); fondos de OpenStreetMap, Esri (satélite) y OpenTopoMap (relieve). Las fotos se cargan desde la carpeta de Google Drive.
- **Tren**: cada tramo sigue las vías reales del 国土数値情報 N02 (MLIT, vía [geolonia/data-jp-railroads](https://github.com/geolonia/data-jp-railroads)), restringido a las líneas que hizo el tren (`tools/rail.py`). Los tramos sin reserva que los confirme salen como "ruta probable".
- **Bici**: la ruta ciclista oficial del Shimanami Kaidō (relación OSM 2236106), más el acceso desde la estación de Imabari calculado con OSRM.
- **Avión**: arcos de círculo máximo entre aeropuertos (no hay traza de vuelo pública).
- **Fotos**: las del celular se ubican por la hora del nombre del archivo; las de la cámara, por número y fecha, revisadas a mano con las miniaturas. Las tomadas en movimiento van en una posición aproximada sobre la ruta.

## Regenerar

```bash
cd tools
python3 rail.py            # necesita out/ de geolonia/data-jp-railroads en ./g
python3 build.py data/drive_list.txt   # lista nombre|id|fecha de la carpeta de Drive
node assemble.js           # escribe site2/index.html
```
