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
    result = {"fields": [f.name() for f in layer.fields()]}
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
