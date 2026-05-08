# Toolbox: SelectionTools

Tools for spatial and attribute-based selection.

### Tool: QgsVectorLayer_selectByExpression
- **Description**: Selects features in a layer using a SQL-like expression.
- **Schema**:
```json
{
    "name": "QgsVectorLayer_selectByExpression",
    "description": "Selects features in a vector layer using a SQL expression.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Layer name."},
            "sql": {"type": "string", "description": "SQL expression"}
        },
        "required": ["layer_name", "sql"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    layer.selectByExpression(args['sql'])
    count = layer.selectedFeatureCount()
    layer.triggerRepaint()
    if count > 0: self.iface.mapCanvas().zoomToSelected(layer)
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "count": count}
else:
    result = {"error": "Layer not found"}
```

### Tool: processing_select_by_location
- **Description**: Selects features in a target layer based on their spatial relationship (e.g. within, intersects) to features in another layer.
- **Schema**:
```json
{
    "name": "processing_select_by_location",
    "description": "Selects features in a target layer based on their spatial relationship (e.g., 'within', 'intersects') to features in an intersect layer. Useful for queries like 'points within a polygon'.",
    "parameters": {
        "type": "object",
        "properties": {
            "target_layer_name": {
                "type": "string",
                "description": "The layer to select features from."
            },
            "intersect_layer_name": {
                "type": "string",
                "description": "The layer to compare spatially against. Only selected features in this layer are used if it has a selection."
            },
            "predicate": {
                "type": "string",
                "enum": ["intersect", "contain", "disjoint", "equal", "touch", "overlap", "are within", "cross"],
                "description": "The spatial relationship to check."
            }
        },
        "required": ["target_layer_name", "intersect_layer_name", "predicate"]
    }
}
```
- **Implementation**:
```python
import processing
from qgis.core import QgsProcessingFeatureSourceDefinition

target_layer = self._resolve_layer(args['target_layer_name'])
intersect_layer = self._resolve_layer(args['intersect_layer_name'])

if target_layer and intersect_layer:
    pred_map = {"intersect": 0, "contain": 1, "disjoint": 2, "equal": 3, "touch": 4, "overlap": 5, "are within": 6, "cross": 7}
    p_val = pred_map.get(args.get('predicate', 'intersect').lower(), 0)
    
    intersect_source = intersect_layer
    if intersect_layer.selectedFeatureCount() > 0:
        intersect_source = QgsProcessingFeatureSourceDefinition(intersect_layer.id(), True)
        
    params = {
        'INPUT': target_layer,
        'PREDICATE': [p_val],
        'INTERSECT': intersect_source,
        'METHOD': 0
    }
    
    try:
        processing.run("native:selectbylocation", params)
        count = target_layer.selectedFeatureCount()
        target_layer.triggerRepaint()
        self.iface.mapCanvas().refresh()
        if count > 0: self.iface.mapCanvas().zoomToSelected(target_layer)
        result = {"status": "success", "selected_count": count}
    except Exception as e:
        result = {"error": f"Processing failed: {str(e)}"}
else:
    result = {"error": "One or both layers not found."}
```

### Tool: clear_selections
- **Description**: Clears all feature selections from a specific vector layer.
- **Schema**:
```json
{
    "name": "clear_selections",
    "description": "Clears all selected features from a vector layer. Leave layer_name empty to clear all layers.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Optional. The layer to clear selections from."}
        }
    }
}
```
- **Implementation**:
```python
name = args.get('layer_name', '')
if not name or name.lower() == 'all':
    count = 0
    for l in QgsProject.instance().mapLayers().values():
        if isinstance(l, QgsVectorLayer):
            l.removeSelection()
            l.triggerRepaint()
            count += 1
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "message": f"Selections cleared from {count} layers."}
else:
    layer = self._resolve_layer(name)
    if layer:
        layer.removeSelection()
        layer.triggerRepaint()
        self.iface.mapCanvas().refresh()
        result = {"status": "success", "message": f"Selections cleared from {layer.name()}"}
    else:
        result = {"error": "Layer not found"}
```
