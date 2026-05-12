# Skill: SelectionTools

Guides the agent through spatial and attribute-based feature selection (SQL expressions, spatial predicates, advanced ranking).

## When to Use
- When the user wants to "find", "highlight", or "select" specific features.
- When performing spatial queries like "points inside this polygon."
- When ranking data (e.g., "select the 5 largest areas").

## Process
1. **Target Identification**: Resolve the target and (if applicable) the intersect layer.
2. **Logic Construction**: Build the SQL expression or spatial predicate.
3. **Execution**: Apply the selection to the layer.
4. **Interaction**: Zoom the map canvas to the selected features for immediate visual feedback.
5. **Verification**: Confirm the count of selected features.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll select all features since I'm not sure about the filter." | **NO.** Always ask for clarification or use a conservative filter. |
| "I don't need to zoom; they can see it in the table." | **NO.** GIS is visual. Always provide map feedback for selections. |
| "I'll call selectByExpression first, then select_features_advanced for the same query." | **STRICT NO.** Pick ONE tool per query. `selectByExpression` = simple WHERE. `select_features_advanced` = top-N ranked. Never both. |
| "After selection, I'll display the selected rows as a table." | **STRICT NO.** After selection, ONLY report the count: 'I have selected X features.' Then STOP. |

## Verification Gates
- **Selection Count**: If 0 features are selected, inform the user and suggest checking field names/values.
- **Canvas Update**: Ensure `triggerRepaint()` and `refresh()` are called.

---

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
    try:
        layer.selectByExpression(args['sql'])
        count = layer.selectedFeatureCount()
        layer.triggerRepaint()
        if count > 0: 
            self.iface.mapCanvas().zoomToSelected(layer)
        self.iface.mapCanvas().refresh()
        
        # Verification Gate
        if count == 0:
            result = {"warning": "Expression was valid but matched 0 features.", "sql_used": args['sql']}
        else:
            result = {"status": "success", "count": count}
    except Exception as e:
        result = {"error": f"SQL Error: {str(e)}"}
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
from qgis.core import QgsVectorLayer
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

### Tool: select_features_advanced
- **Description**: Selects features in a layer with support for filtering, sorting, and limits (e.g. "select the top 5 largest areas").
- **Schema**:
```json
{
    "name": "select_features_advanced",
    "description": "Selects features in a vector layer with advanced options like sorting and limits.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Layer name."},
            "filter": {"type": "string", "description": "Optional SQL expression to filter features."},
            "sort_by": {"type": "string", "description": "Optional field name to sort by."},
            "ascending": {"type": "boolean", "description": "Sort order (default true)."},
            "limit": {"type": "integer", "description": "Optional limit on number of features to select."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
from qgis.core import QgsFeatureRequest
layer = self._resolve_layer(args['layer_name'])
if layer:
    req = QgsFeatureRequest()
    limit = args.get('limit')
    if limit:
        req.setLimit(limit)
        
    if args.get('filter'):
        req.setFilterExpression(args['filter'])
    if args.get('sort_by'):
        req.setOrderBy(QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(args['sort_by'], args.get('ascending', True))]))
    
    ids = [feat.id() for feat in layer.getFeatures(req)]
    
    layer.select(ids)
    count = len(ids)
    layer.triggerRepaint()
    if count > 0: self.iface.mapCanvas().zoomToSelected(layer)
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "selected_count": count}
else:
    result = {"error": "Layer not found"}
```
