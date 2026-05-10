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
            "limit": {"type": "integer", "description": "Number of features to return (default 10)."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    if hasattr(layer, 'getFeatures'):
        limit = args.get('limit', 10)
        fields = [f.name() for f in layer.fields()]
        data = []
        for feat in layer.getFeatures():
            if len(data) >= limit: break
            row = {}
            for i, f in enumerate(fields):
                val = feat.attributes()[i]
                if hasattr(val, 'toString'): val = val.toString()
                row[f] = str(val)
            data.append(row)
        result = {"features": data, "count": len(data)}
    else:
        result = {"error": f"Layer '{layer.name()}' has no attribute table (it may be a raster layer)."}
else:
    result = {"error": "Layer not found"}
```
