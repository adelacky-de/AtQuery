# Toolbox: VectorProcessing

Core vector geoprocessing algorithms.

### Tool: processing_run_native_buffer
- **Description**: Creates a buffer around features in a vector layer.
- **Schema**:
```json
{
    "name": "processing_run_native_buffer",
    "description": "Runs the QGIS native buffer algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "distance": {"type": "number", "description": "Buffer distance in layer units."}
        },
        "required": ["layer_name", "distance"]
    }
}
```
- **Implementation**:
```python
import processing
from qgis.core import QgsUnitTypes
layer = self._resolve_layer(args['layer_name'])
if layer:
    dist = args['distance']
    # Check if the layer uses degrees
    if layer.crs().mapUnits() == QgsUnitTypes.DistanceDegrees:
        # Very rough approximation for meters to degrees
        dist = dist / 111319.9
        
    res = processing.run("native:buffer", {
        'INPUT': layer, 
        'DISTANCE': dist, 
        'SEGMENTS': 5,
        'END_CAP_STYLE': 0,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'DISSOLVE': False,
        'OUTPUT': 'memory:'
    })
    QgsProject.instance().addMapLayer(res['OUTPUT'])
    result = {"status": "success", "layer_name": res['OUTPUT'].name(), "distance_used": dist}
else:
    result = {"error": "Layer not found"}
```
### Tool: extract_selected_features
- **Description**: Creates a new memory layer from the currently selected features of a layer.
- **Schema**:
```json
{
    "name": "extract_selected_features",
    "description": "Extracts the selected features from a layer into a new memory layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Name of the source layer."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['layer_name'])
if layer:
    if layer.selectedFeatureCount() == 0:
        result = {"error": "No features selected in layer."}
    else:
        res = processing.run("native:saveselectedfeatures", {'INPUT': layer, 'OUTPUT': 'memory:'})
        QgsProject.instance().addMapLayer(res['OUTPUT'])
        result = {"status": "success", "new_layer": res['OUTPUT'].name()}
else:
    result = {"error": "Layer not found"}
```
