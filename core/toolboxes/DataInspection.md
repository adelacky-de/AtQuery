# Toolbox: DataInspection

Detailed metadata about layers, their fields, attributes, and Coordinate Reference Systems.

### Tool: QgsVectorLayer_fields
- **Description**: Lists all field names and types for a given layer.
- **Schema**:
```json
{
    "name": "QgsVectorLayer_fields",
    "description": "Returns a list of field names for the specified layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    if hasattr(layer, 'fields'):
        result = {"fields": [f.name() for f in layer.fields()]}
    else:
        result = {"error": f"Layer '{layer.name()}' is not a vector layer and has no attribute fields."}
else:
    result = {"error": "Layer not found"}
```

### Tool: QgsVectorLayer_crs
- **Description**: Returns the Coordinate Reference System (CRS) of a layer.
- **Schema**:
```json
{
    "name": "QgsVectorLayer_crs",
    "description": "Returns the Coordinate Reference System (CRS) of a layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    result = {"crs": layer.crs().authid(), "description": layer.crs().description()}
else:
    result = {"error": "Layer not found"}
```

### Tool: get_layer_features_sample
- **Description**: Returns a sample of features (rows) from the layer's attribute table.
- **Schema**:
```json
{
    "name": "get_layer_features_sample",
    "description": "Returns a sample of attribute values (first 10 rows) for the specified layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."},
            "limit": {"type": "integer", "description": "Number of features to return (default 5, max 50)."},
            "sort_by": {"type": "string", "description": "Field name to sort by."},
            "ascending": {"type": "boolean", "description": "Sort order (default true)."}
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
    if hasattr(layer, 'getFeatures'):
        # Clamp limit between 1 and 50 to prevent crashing local LLMs
        limit = min(max(args.get('limit', 5), 1), 50)
        fields = [f.name() for f in layer.fields()]
        
        req = QgsFeatureRequest()
        sort_field = args.get('sort_by')
        if sort_field:
            req.setOrderBy(QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(sort_field, args.get('ascending', True))]))
        
        # Build HTML table for premium look and to prevent AI hallucination
        html = '<table border="1" style="border-collapse: collapse; width: 100%; font-size: 11px;">'
        html += '<tr style="background-color: #f2f2f2;">' + "".join([f'<th style="padding: 4px;">{f}</th>' for f in fields]) + '</tr>'
        
        count = 0
        for feat in layer.getFeatures(req):
            if count >= limit: break
            html += '<tr>' + "".join([f'<td style="padding: 4px;">{str(feat.attributes()[i])}</td>' for i in range(len(fields))]) + '</tr>'
            count += 1
        html += '</table>'
        
        if count == 0:
            result = {"error": "The layer is empty (0 features)."}
        else:
            result = {"status": "success", "html_table": html}
    else:
        result = {"error": f"Layer '{layer.name()}' has no attribute table (it may be a raster layer)."}
else:
    result = {"error": "Layer not found"}
```
