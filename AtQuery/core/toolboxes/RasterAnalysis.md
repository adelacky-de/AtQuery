# Toolbox: RasterAnalysis

Tools for processing and analyzing raster data.

### Tool: gdal_slope
- **Description**: Calculates the slope from an elevation raster.
- **Schema**:
```json
{
    "name": "gdal_slope",
    "description": "Calculates slope from a DEM layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer": {"type": "string", "description": "DEM layer name."}
        },
        "required": ["input_layer"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['input_layer'])
if layer:
    res = processing.run("gdal:slope", {'INPUT': layer, 'BAND': 1, 'OUTPUT': 'memory:'})
    QgsProject.instance().addMapLayer(res['OUTPUT'])
    result = {"status": "success", "layer": res['OUTPUT'].name()}
else:
    result = {"error": "Layer not found"}
```

### Tool: gdal_hillshade
- **Description**: Generates a hillshade from an elevation raster.
- **Schema**:
```json
{
    "name": "gdal_hillshade",
    "description": "Generates a hillshade from a DEM layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer": {"type": "string"}
        },
        "required": ["input_layer"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['input_layer'])
if layer:
    res = processing.run("gdal:hillshade", {'INPUT': layer, 'BAND': 1, 'Z_FACTOR': 1, 'AZIMUTH': 315, 'ALTITUDE': 45, 'OUTPUT': 'memory:'})
    QgsProject.instance().addMapLayer(res['OUTPUT'])
    result = {"status": "success", "layer": res['OUTPUT'].name()}
else:
    result = {"error": "Layer not found"}
```
