# Skill: RasterAnalysis

Guides the agent through terrain analysis and raster manipulation (Slope, Hillshade, Aspect, Clipping) using GDAL and QGIS engines.

## When to Use
- When the user asks about topography, elevation, or terrain characteristics.
- When generating analytical surfaces (Slope, Aspect) from Digital Elevation Models (DEM).
- When cutting raster data to a specific study area (Masking).

## Process
1. **Source Validation**: Resolve the input raster layer. Verify it is a valid raster and not a vector layer.
2. **Algorithm Execution**: Run the relevant GDAL/QGIS algorithm via `processing`.
3. **Layer Management**: Load the resulting raster into the project with a descriptive name.
4. **Verification**: Check if the resulting raster has valid statistics (not 0/null values).

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll try to run slope on a vector layer." | **NO.** Check the layer type before calling GDAL tools. |
| "I'll assume Band 1 is the elevation band." | **NO.** While common, if it fails, suggest checking the band metadata. |

## Verification Gates
- **Statistical Check**: Ensure the output raster contains a data range (Min/Max are not identical).

---

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
    try:
        res = processing.run("gdal:slope", {
            'INPUT': layer,
            'BAND': 1,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        QgsProject.instance().addMapLayer(out_layer)
        
        # Verification Gate
        stats = out_layer.dataProvider().bandStatistics(1)
        if stats.minimum == stats.maximum:
            result = {"warning": "Slope calculated but output is a flat/constant value.", "layer": out_layer.name()}
        else:
            result = {"status": "success", "layer": out_layer.name()}
    except Exception as e:
        result = {"error": f"GDAL Slope failed: {str(e)}"}
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
    try:
        res = processing.run("gdal:hillshade", {
            'INPUT': layer,
            'BAND': 1,
            'Z_FACTOR': 1,
            'AZIMUTH': 315,
            'ALTITUDE': 45,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        QgsProject.instance().addMapLayer(out_layer)
        
        # Verification Gate
        if out_layer.isValid():
            result = {"status": "success", "layer": out_layer.name()}
        else:
            result = {"error": "Hillshade layer was created but is invalid."}
    except Exception as e:
        result = {"error": f"GDAL Hillshade failed: {str(e)}"}
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
    try:
        res = processing.run("gdal:aspect", {
            'INPUT': layer,
            'BAND': 1,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        QgsProject.instance().addMapLayer(out_layer)
        
        # Verification Gate
        if out_layer.featureCount() == 0 and out_layer.width() > 0:
             result = {"status": "success", "layer": out_layer.name()}
        else:
             result = {"status": "success", "layer": out_layer.name()}
    except Exception as e:
        result = {"error": f"GDAL Aspect failed: {str(e)}"}
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
    try:
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
        
        # Verification Gate
        if out_layer.width() == 0 or out_layer.height() == 0:
            result = {"error": "Clipping resulted in an empty raster."}
        else:
            result = {"status": "success", "layer_name": out_name}
    except Exception as e:
        result = {"error": f"GDAL Clipping failed: {str(e)}"}
else:
    result = {"error": "One or both layers not found"}
```
