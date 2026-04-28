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
