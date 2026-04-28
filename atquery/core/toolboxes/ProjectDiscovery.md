# ProjectDiscovery Toolbox
Keywords: layers, extent, project, map, list, what is in

## QgsProject_mapLayers
- **Description**: Lists all layer names in the current QGIS project.
- **Keywords**: list layers, what layers, show layers, map layers
- **Schema**:
```json
{
    "name": "QgsProject_mapLayers",
    "description": "Lists all layer names in the current QGIS project.",
    "parameters": {
        "type": "object",
        "properties": {
            "refresh": {"type": "boolean", "description": "Force refresh."}
        }
    }
}
```

## QgsProject_extent
- **Description**: Returns the bounding box of the entire project.
- **Keywords**: project extent, map bounding box, overall extent
- **Schema**:
```json
{
    "name": "QgsProject_extent",
    "description": "Returns the bounding box of the entire project.",
    "parameters": {"type": "object", "properties": {}}
}
```
