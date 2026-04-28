# SelectionTools Toolbox
Keywords: select, filter, query, where, expression, location, intersect, contains

## QgsVectorLayer_selectByExpression
- **Description**: Selects features based on an SQL-like query.
- **Keywords**: filter layer, select features, sql query, layer selection
- **Schema**:
```json
{
    "name": "QgsVectorLayer_selectByExpression",
    "description": "Selects features based on an SQL-like query.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "sql": {"type": "string", "description": "SQL filter e.g. \"field\" = 'value'"}
        },
        "required": ["layer_name", "sql"]
    }
}
```

## processing_run_selectbylocation
- **Description**: Spatial selection between layers.
- **Keywords**: select by location, spatial selection, intersect selection, features inside
- **Schema**:
```json
{
    "name": "processing_run_selectbylocation",
    "description": "Spatial selection between layers.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "predicate": {"type": "string", "description": "intersect, contains, etc."},
            "intersect_layer_name": {"type": "string"}
        },
        "required": ["input_layer_name", "predicate", "intersect_layer_name"]
    }
}
```
