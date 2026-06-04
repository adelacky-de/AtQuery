# Toolbox: ExportTools

Tools for exporting layers and map layouts to files.

### Tool: export_layer_to_file
- **Description**: Exports a vector layer to various formats (GeoJSON, CSV, GeoPackage, Shapefile, PostgreSQL, KML, DXF, etc.).
- **Schema**:
```json
{
    "name": "export_layer_to_file",
    "description": "Exports a vector layer to a file or database. Supports GeoJSON, CSV, GeoPackage, ESRI Shapefile, PostgreSQL, KML, DXF.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "format": {"type": "string", "description": "Format to export to, e.g., 'GeoJSON', 'CSV', 'GeoPackage', 'ESRI Shapefile', 'PostgreSQL'"},
            "file_name": {"type": "string", "description": "The name of the file to save (e.g., 'layer_name.geojson'). DO NOT use generic names like 'output.geojson'. If no path is provided, it saves to the QGIS project directory."}
        },
        "required": ["layer_name", "format", "file_name"]
    }
}
```
- **Implementation**:
```python
import os
from qgis.core import QgsVectorFileWriter, QgsProject

layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": "Layer not found"}
else:
    fmt = args.get('format', 'GeoJSON').lower()
    file_name = args.get('file_name', 'export.geojson')
    
    # Resolve project path
    proj_path = QgsProject.instance().homePath()
    if not proj_path:
        # Fallback to user home dir if project isn't saved
        proj_path = os.path.expanduser("~")
        
    if not os.path.isabs(file_name):
        file_name = os.path.join(proj_path, file_name)
        
    driver_map = {
        'geojson': ('GeoJSON', '.geojson'),
        'csv': ('CSV', '.csv'),
        'geopackage': ('GPKG', '.gpkg'),
        'gpkg': ('GPKG', '.gpkg'),
        'shapefile': ('ESRI Shapefile', '.shp'),
        'esri shapefile': ('ESRI Shapefile', '.shp'),
        'kml': ('KML', '.kml'),
        'dxf': ('DXF', '.dxf'),
        'postgresql': ('PostgreSQL', ''),
        'postgis': ('PostgreSQL', '')
    }
    driver_name, ext = driver_map.get(fmt, ('GeoJSON', '.geojson'))
    
    # Force extension if not database, and FORCE file_name to be the exact full layer name
    if ext:
        file_name = f"{layer.name()}{ext}"
        if proj_path:
            file_name = os.path.join(proj_path, file_name)
    
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = driver_name
    
    err, err_msg = QgsVectorFileWriter.writeAsVectorFormatV2(layer, file_name, self.iface.mapCanvas().mapSettings().transformContext(), options)
    
    if err == QgsVectorFileWriter.NoError:
        result = {"status": "success", "saved_to": file_name, "driver": driver_name, "exported_layer": layer.name()}
    else:
        result = {"error": f"Export failed: {err_msg}"}
```

### Tool: export_map_canvas
- **Description**: Saves the current QGIS map canvas view to an image file (PNG, JPG, PDF).
- **Schema**:
```json
{
    "name": "export_map_canvas",
    "description": "Saves the current map view to an image file (PNG, PDF, etc.).",
    "parameters": {
        "type": "object",
        "properties": {
            "file_name": {"type": "string", "description": "The name of the file to save (e.g., 'map.png' or 'map.pdf'). If no path is provided, it saves to the QGIS project directory."}
        },
        "required": ["file_name"]
    }
}
```
- **Implementation**:
```python
import os
from qgis.core import QgsProject

file_name = args.get('file_name', 'map_export.png')

# Resolve project path
proj_path = QgsProject.instance().homePath()
if not proj_path:
    proj_path = os.path.expanduser("~")
    
if not os.path.isabs(file_name):
    file_name = os.path.join(proj_path, file_name)

try:
    self.iface.mapCanvas().saveAsImage(file_name)
    result = {"status": "success", "saved_to": file_name}
except Exception as e:
    result = {"error": f"Export failed: {str(e)}"}
```
