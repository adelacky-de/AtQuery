# DataInspection Toolbox
Keywords: fields, attributes, columns, crs, projection, coordinate system

## QgsVectorLayer_fields
- **Description**: Retrieves field names for a specific layer.
- **Keywords**: list fields, layer attributes, column names, what fields
- **Schema**:
```json
{
    "name": "QgsVectorLayer_fields",
    "description": "Retrieves field names for a specific layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```

## QgsVectorLayer_crs
- **Description**: Returns the Coordinate Reference System (CRS) of a layer.
- **Keywords**: layer crs, layer projection, check projection, coordinate system
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
