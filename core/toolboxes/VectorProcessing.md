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
    # Check if the layer uses degrees — convert meters to degrees
    if layer.crs().mapUnits() == QgsUnitTypes.DistanceDegrees:
        dist = dist / 111319.9
    
    out_name = f"{layer.name()}_{int(args['distance'])}m_buffer"
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
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name, "distance_used": dist}
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
        out_name = args.get('output_name') or f"{layer.name()}_selection"
        res = processing.run("native:saveselectedfeatures", {
            'INPUT': layer,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        out_layer.setName(out_name)
        QgsProject.instance().addMapLayer(out_layer)
        result = {"status": "success", "new_layer": out_name}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_dissolve
- **Description**: Dissolves features in a vector layer based on a specific field or all features.
- **Schema**:
```json
{
    "name": "processing_run_native_dissolve",
    "description": "Runs the QGIS native dissolve algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "field_name": {"type": "string", "description": "Optional field name to dissolve by. Leave empty to dissolve all features into one."}
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
    field = args.get('field_name', '')
    fields_list = [field] if field else []
    
    out_name = f"{layer.name()}_dissolved"
    res = processing.run("native:dissolve", {
        'INPUT': layer,
        'FIELD': fields_list,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_difference
- **Description**: Extracts features from the input layer that don't fall within the overlay layer (Exclude).
- **Schema**:
```json
{
    "name": "processing_run_native_difference",
    "description": "Runs the QGIS native difference algorithm to exclude areas of an overlay layer from the input layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "overlay_layer_name": {"type": "string"}
        },
        "required": ["input_layer_name", "overlay_layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
input_layer = self._resolve_layer(args['input_layer_name'])
overlay_layer = self._resolve_layer(args['overlay_layer_name'])

if input_layer and overlay_layer:
    out_name = f"{input_layer.name()}_difference"
    res = processing.run("native:difference", {
        'INPUT': input_layer,
        'OVERLAY': overlay_layer,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "One or both layers not found"}
```

### Tool: processing_run_native_bounding_boxes
- **Description**: Calculates the bounding boxes (minimum bounding geometry) for features in a layer.
- **Schema**:
```json
{
    "name": "processing_run_native_bounding_boxes",
    "description": "Runs the QGIS native bounding boxes algorithm to create extent polygons.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"}
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
    out_name = f"{layer.name()}_bbox"
    res = processing.run("native:boundingboxes", {
        'INPUT': layer,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_join_attributes_by_location
- **Description**: Joins attributes from a join layer to an input layer based on spatial relationship.
- **Schema**:
```json
{
    "name": "processing_run_native_join_attributes_by_location",
    "description": "Runs QGIS native join attributes by location algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string", "description": "Layer to add attributes to."},
            "join_layer_name": {"type": "string", "description": "Layer to pull attributes from."},
            "predicate": {
                "type": "string",
                "enum": ["intersect", "contain", "equal", "touch", "overlap", "are within", "cross"],
                "description": "Spatial relationship."
            }
        },
        "required": ["input_layer_name", "join_layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
input_layer = self._resolve_layer(args['input_layer_name'])
join_layer = self._resolve_layer(args['join_layer_name'])

if input_layer and join_layer:
    pred_map = {"intersect": 0, "contain": 1, "equal": 3, "touch": 4, "overlap": 5, "are within": 6, "cross": 7}
    p_val = pred_map.get(args.get('predicate', 'intersect').lower(), 0)
    
    out_name = f"{input_layer.name()}_joined"
    res = processing.run("native:joinattributesbylocation", {
        'INPUT': input_layer,
        'JOIN': join_layer,
        'PREDICATE': [p_val],
        'JOIN_FIELDS': [],
        'METHOD': 0,
        'DISCARD_NONMATCHING': False,
        'PREFIX': 'join_',
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "One or both layers not found"}
```

### Tool: processing_run_native_clip
- **Description**: Clips a vector layer using the polygons of an overlay layer.
- **Schema**:
```json
{
    "name": "processing_run_native_clip",
    "description": "Runs the QGIS native clip algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "overlay_layer_name": {"type": "string"}
        },
        "required": ["input_layer_name", "overlay_layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
input_layer = self._resolve_layer(args['input_layer_name'])
overlay_layer = self._resolve_layer(args['overlay_layer_name'])

if input_layer and overlay_layer:
    out_name = f"{input_layer.name()}_clipped"
    res = processing.run("native:clip", {
        'INPUT': input_layer,
        'OVERLAY': overlay_layer,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "One or both layers not found"}
```

### Tool: processing_run_native_centroids
- **Description**: Creates a new point layer representing the centroids of the input features.
- **Schema**:
```json
{
    "name": "processing_run_native_centroids",
    "description": "Runs the QGIS native centroids algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"}
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
    out_name = f"{layer.name()}_centroids"
    res = processing.run("native:centroids", {
        'INPUT': layer,
        'ALL_PARTS': False,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_intersection
- **Description**: Extracts the overlapping portions of features in the input and overlay layers, keeping attributes from both.
- **Schema**:
```json
{
    "name": "processing_run_native_intersection",
    "description": "Runs the QGIS native intersection algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "overlay_layer_name": {"type": "string"}
        },
        "required": ["input_layer_name", "overlay_layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
input_layer = self._resolve_layer(args['input_layer_name'])
overlay_layer = self._resolve_layer(args['overlay_layer_name'])

if input_layer and overlay_layer:
    out_name = f"{input_layer.name()}_intersected"
    res = processing.run("native:intersection", {
        'INPUT': input_layer,
        'OVERLAY': overlay_layer,
        'INPUT_FIELDS': [],
        'OVERLAY_FIELDS': [],
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "One or both layers not found"}
```

### Tool: processing_run_native_reproject
- **Description**: Reprojects a vector layer to a different Coordinate Reference System (CRS).
- **Schema**:
```json
{
    "name": "processing_run_native_reproject",
    "description": "Runs the QGIS native reprojectlayer algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "target_crs": {"type": "string", "description": "Target CRS string, e.g. 'EPSG:4326' or 'EPSG:3857'."}
        },
        "required": ["layer_name", "target_crs"]
    }
}
```
- **Implementation**:
```python
import processing
from qgis.core import QgsCoordinateReferenceSystem

layer = self._resolve_layer(args['layer_name'])
if layer:
    crs_str = args['target_crs']
    crs = QgsCoordinateReferenceSystem(crs_str)
    if not crs.isValid():
        result = {"error": f"Invalid CRS: {crs_str}"}
    else:
        out_name = f"{layer.name()}_{crs_str.replace(':', '')}"
        res = processing.run("native:reprojectlayer", {
            'INPUT': layer,
            'TARGET_CRS': crs,
            'OUTPUT': 'memory:'
        })
        out_layer = res['OUTPUT']
        out_layer.setName(out_name)
        QgsProject.instance().addMapLayer(out_layer)
        result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "Layer not found"}
```
