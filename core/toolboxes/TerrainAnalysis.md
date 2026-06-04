# Toolbox: TerrainAnalysis

Advanced terrain and surface modeling (TIN, Contours).

### Tool: gdal_contour
- **Description**: Generates contours from a raster elevation layer.
- **Schema**:
```json
{
    "name": "gdal_contour",
    "description": "Generates contour lines from a DEM.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer": {"type": "string"},
            "interval": {"type": "number", "description": "Contour interval."}
        },
        "required": ["input_layer", "interval"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['input_layer'])
if layer:
    res = processing.run("gdal:contour", {'INPUT': layer, 'BAND': 1, 'INTERVAL': args['interval'], 'FIELD_NAME': 'ELEV', 'OUTPUT': 'memory:'})
    QgsProject.instance().addMapLayer(res['OUTPUT'])
    result = {"status": "success", "layer": res['OUTPUT'].name()}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_qgis_tin_interpolation
- **Description**: Creates a TIN (Triangulated Irregular Network) interpolation raster from vector points.
- **Schema**:
```json
{
    "name": "processing_run_qgis_tin_interpolation",
    "description": "Creates a TIN DEM raster from a vector point or line layer containing elevation data.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "elevation_field": {"type": "string", "description": "The attribute field containing Z/elevation values."}
        },
        "required": ["layer_name", "elevation_field"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['layer_name'])
if layer:
    elev_field = args['elevation_field']
    interp_data = f"{layer.id()}::~::{elev_field}::~::0::~::"
    
    ext = layer.extent()
    pixel_size = max(ext.width(), ext.height()) / 1000.0
    if pixel_size == 0: pixel_size = 1
    
    out_name = f"{layer.name()}_TIN"
    try:
        res = processing.run("qgis:tininterpolation", {
            'INTERPOLATION_DATA': interp_data,
            'METHOD': 0,
            'EXTENT': ext.toString(),
            'PIXEL_SIZE': pixel_size,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        out_layer.setName(out_name)
        QgsProject.instance().addMapLayer(out_layer)
        result = {"status": "success", "layer_name": out_name}
    except Exception as e:
        result = {"error": f"TIN Interpolation failed: {str(e)}. Make sure the elevation field exists and contains numeric values."}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_qgis_idw_interpolation
- **Description**: Creates an IDW (Inverse Distance Weighting) interpolation raster from vector points.
- **Schema**:
```json
{
    "name": "processing_run_qgis_idw_interpolation",
    "description": "Creates an IDW DEM raster from a vector point layer containing elevation data.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "elevation_field": {"type": "string", "description": "The attribute field containing Z/elevation values."}
        },
        "required": ["layer_name", "elevation_field"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['layer_name'])
if layer:
    elev_field = args['elevation_field']
    interp_data = f"{layer.id()}::~::{elev_field}::~::0::~::"
    ext = layer.extent()
    pixel_size = max(ext.width(), ext.height()) / 1000.0
    if pixel_size == 0: pixel_size = 1
    
    out_name = f"{layer.name()}_IDW"
    try:
        res = processing.run("qgis:idwinterpolation", {
            'INTERPOLATION_DATA': interp_data,
            'DISTANCE_COEFFICIENT': 2,
            'EXTENT': ext.toString(),
            'PIXEL_SIZE': pixel_size,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        out_layer.setName(out_name)
        QgsProject.instance().addMapLayer(out_layer)
        result = {"status": "success", "layer_name": out_name}
    except Exception as e:
        result = {"error": f"IDW Interpolation failed: {str(e)}."}
else:
    result = {"error": "Layer not found"}
```
