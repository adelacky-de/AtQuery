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

### Tool: processing_run_native_extent_to_layer
- **Description**: Calculates the extent (bounding box) of a layer and creates a polygon.
- **Schema**:
```json
{
    "name": "processing_run_native_extent_to_layer",
    "description": "Calculates the extent (bounding box) of a layer and creates a polygon. If 'use_canvas_extent' is true, it uses the current map canvas extent instead.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "The layer to get the extent from."},
            "use_canvas_extent": {"type": "boolean", "description": "Set to true to use the current map canvas view extent instead of a specific layer's extent."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
import processing
from qgis.core import QgsProject

if args.get('use_canvas_extent', False):
    extent_str = self.iface.mapCanvas().extent().toString() + f" [{self.iface.mapCanvas().mapSettings().destinationCrs().authid()}]"
    out_name = "canvas_extent"
    res = processing.run("native:extenttolayer", {
        'INPUT': extent_str,
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    layer = self._resolve_layer(args['layer_name'])
    if layer:
        out_name = f"{layer.name()}_extent"
        res = processing.run("native:extenttolayer", {
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

### Tool: processing_run_native_extract_by_expression
- **Description**: Extracts features from a vector layer matching a SQL expression.
- **Schema**:
```json
{
    "name": "processing_run_native_extract_by_expression",
    "description": "Extracts features from a vector layer matching a SQL expression into a new layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "expression": {"type": "string", "description": "SQL expression to filter features. IMPORTANT: Use double quotes for field names and single quotes for string values (e.g. \"FIELD_NAME\" = 'Value')."}
        },
        "required": ["layer_name", "expression"]
    }
}
```
- **Implementation**:
```python
import processing
layer = self._resolve_layer(args['layer_name'])
if layer:
    out_name = f"{layer.name()}_extracted"
    res = processing.run("native:extractbyexpression", {
        'INPUT': layer,
        'EXPRESSION': args['expression'],
        'OUTPUT': 'memory:'
    })
    out_layer = res['OUTPUT']
    out_layer.setName(out_name)
    QgsProject.instance().addMapLayer(out_layer)
    result = {"status": "success", "layer_name": out_name}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_join_attributes_by_field
- **Description**: Performs a table join between two layers using a common key field.
- **Schema**:
```json
{
    "name": "processing_run_native_join_attributes_by_field",
    "description": "Performs an attribute table join between an input layer and a join layer using a common key field.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "input_field": {"type": "string", "description": "Key field in the input layer."},
            "join_layer_name": {"type": "string"},
            "join_field": {"type": "string", "description": "Key field in the join layer."},
            "inner_join": {"type": "boolean", "description": "Set to true to discard records that don't match (Inner Join), or false to keep all input records (Left Outer Join)."}
        },
        "required": ["input_layer_name", "input_field", "join_layer_name", "join_field", "inner_join"]
    }
}
```
- **Implementation**:
```python
import processing
input_layer = self._resolve_layer(args['input_layer_name'])
join_layer = self._resolve_layer(args['join_layer_name'])

if input_layer and join_layer:
    out_name = f"{input_layer.name()}_joined"
    discard_nonmatching = args.get('inner_join', False)
    
    res = processing.run("native:joinattributestable", {
        'INPUT': input_layer,
        'FIELD': args['input_field'],
        'INPUT_2': join_layer,
        'FIELD_2': args['join_field'],
        'FIELDS_TO_COPY': [],
        'METHOD': 1,
        'DISCARD_NONMATCHING': discard_nonmatching,
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

### Tool: processing_run_native_symmetricaldifference
- **Description**: Extracts the non-overlapping portions of features in the input and overlay layers.
- **Schema**:
```json
{
    "name": "processing_run_native_symmetricaldifference",
    "description": "Runs the QGIS native symmetrical difference algorithm (finds areas that do NOT overlap).",
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
    out_name = f"{input_layer.name()}_symdiff"
    res = processing.run("native:symmetricaldifference", {
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

### Tool: processing_run_native_splitvectorlayer
- **Description**: Splits a single layer into multiple layers based on a unique attribute field.
- **Schema**:
```json
{
    "name": "processing_run_native_splitvectorlayer",
    "description": "Runs the QGIS native split vector layer algorithm.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "field": {"type": "string", "description": "The attribute field to split by."},
            "output_directory": {"type": "string", "description": "Directory to save the split files. If not provided, saves to project directory."}
        },
        "required": ["layer_name", "field"]
    }
}
```
- **Implementation**:
```python
import processing, os
from qgis.core import QgsProject

layer = self._resolve_layer(args['layer_name'])
if layer:
    out_dir = args.get('output_directory', '')
    if not out_dir:
        out_dir = QgsProject.instance().homePath()
        if not out_dir: out_dir = os.path.expanduser("~")
        out_dir = os.path.join(out_dir, f"{layer.name()}_split")
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        
    res = processing.run("native:splitvectorlayer", {
        'INPUT': layer,
        'FIELD': args['field'],
        'FILE_TYPE': 1,
        'OUTPUT': out_dir
    })
    result = {"status": "success", "saved_to": out_dir}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_run_native_fixgeometries
- **Description**: Fixes invalid geometries (e.g., self-intersections).
- **Schema**:
```json
{
    "name": "processing_run_native_fixgeometries",
    "description": "Runs the QGIS native fix geometries algorithm.",
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
    out_name = f"{layer.name()}_fixed"
    res = processing.run("native:fixgeometries", {
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

### Tool: processing_run_native_convexhull
- **Description**: Generates a convex hull around features.
- **Schema**:
```json
{
    "name": "processing_run_native_convexhull",
    "description": "Runs the QGIS native convex hull algorithm.",
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
    out_name = f"{layer.name()}_convexhull"
    res = processing.run("native:convexhull", {
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

### Tool: processing_run_native_linestopolygons
- **Description**: Converts line features into polygon features.
- **Schema**:
```json
{
    "name": "processing_run_native_linestopolygons",
    "description": "Runs the QGIS native lines to polygons algorithm.",
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
    out_name = f"{layer.name()}_polygons"
    res = processing.run("native:linestopolygons", {
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

### Tool: processing_run_native_polygonstolines
- **Description**: Converts polygon features into line boundary features.
- **Schema**:
```json
{
    "name": "processing_run_native_polygonstolines",
    "description": "Runs the QGIS native polygons to lines algorithm.",
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
    out_name = f"{layer.name()}_lines"
    res = processing.run("native:polygonstolines", {
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
