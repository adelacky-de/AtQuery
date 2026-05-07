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

### Tool: gdal_aspect
- **Description**: Calculates aspect from an elevation raster.
- **Schema**:
```json
{
    "name": "gdal_aspect",
    "description": "Calculates aspect (orientation of slope) from a DEM layer.",
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
    res = processing.run("gdal:aspect", {'INPUT': layer, 'BAND': 1, 'OUTPUT': 'memory:'})
    QgsProject.instance().addMapLayer(res['OUTPUT'])
    result = {"status": "success", "layer": res['OUTPUT'].name()}
else:
    result = {"error": "Layer not found"}
```

### Tool: gdal_clip_raster_by_mask
- **Description**: Clips a raster layer using a polygon mask layer.
- **Schema**:
```json
{
    "name": "gdal_clip_raster_by_mask",
    "description": "Clips a raster using a vector polygon mask layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_raster": {"type": "string"},
            "mask_layer": {"type": "string"}
        },
        "required": ["input_raster", "mask_layer"]
    }
}
```
- **Implementation**:
```python
import processing
raster_layer = self._resolve_layer(args['input_raster'])
mask_layer = self._resolve_layer(args['mask_layer'])

if raster_layer and mask_layer:
    out_name = f"{raster_layer.name()}_clipped"
    res = processing.run("gdal:cliprasterbymasklayer", {
        'INPUT': raster_layer,
        'MASK': mask_layer,
        'KEEP_RESOLUTION': True,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "One or both layers not found"}
```
