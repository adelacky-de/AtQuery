# VectorProcessing Toolbox
Keywords: buffer, clip, reproject, join, merge, dissolve

## processing_run_native_buffer
- **Description**: Creates a buffer zone around features.
- **Keywords**: buffer, create buffer, distance zone, proximity
- **Schema**:
```json
{
    "name": "processing_run_native_buffer",
    "description": "Creates a buffer zone around features.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "distance": {"type": "number"},
            "output_layer_name": {"type": "string"}
        },
        "required": ["layer_name", "distance"]
    }
}
```

## processing_run_reprojectlayer
- **Description**: Reprojects a layer to a different CRS.
- **Keywords**: reproject, change crs, transform layer, coordinate transform
- **Schema**:
```json
{
    "name": "processing_run_reprojectlayer",
    "description": "Reprojects a layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string"},
            "target_crs": {"type": "string"}
        },
        "required": ["layer_name", "target_crs"]
    }
}
```

## processing_run_native_clip
- **Description**: Clips a layer using another layer's geometry.
- **Keywords**: clip, crop, cut layer, overlay clip
- **Schema**:
```json
{
    "name": "processing_run_native_clip",
    "description": "Clips a layer using another layer's geometry.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer": {"type": "string"},
            "overlay_layer": {"type": "string"},
            "output": {"type": "string", "description": "memory: or file path"}
        },
        "required": ["input_layer", "overlay_layer"]
    }
}
```

## processing_run_joinattributestable
- **Description**: Joins attributes from another table/layer.
- **Keywords**: join, merge attributes, attribute join, table join
- **Schema**:
```json
{
    "name": "processing_run_joinattributestable",
    "description": "Joins attributes from a secondary layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "input_layer_name": {"type": "string"},
            "join_layer_name": {"type": "string"},
            "input_join_field": {"type": "string"},
            "join_layer_field": {"type": "string"},
            "join_prefix": {"type": "string"}
        },
        "required": ["input_layer_name", "join_layer_name", "input_join_field", "join_layer_field"]
    }
}
```
