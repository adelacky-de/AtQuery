# WebServices Toolbox
Keywords: wms, wfs, xyz, tiles, google maps, osm, remote, server

## QgsProject_addWmsLayer
- **Description**: Adds a WMS (Web Map Service) layer to the project.
- **Keywords**: add wms, web map service, remote layer
- **Schema**:
```json
{
    "name": "QgsProject_addWmsLayer",
    "description": "Adds a WMS layer to the project.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "layer_name": {"type": "string"},
            "format": {"type": "string", "default": "image/png"}
        },
        "required": ["url", "layer_name"]
    }
}
```

## QgsProject_addWfsLayer
- **Description**: Adds a WFS (Web Feature Service) layer.
- **Keywords**: add wfs, web feature service, vector service
- **Schema**:
```json
{
    "name": "QgsProject_addWfsLayer",
    "description": "Adds a WFS layer to the project.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "typename": {"type": "string"}
        },
        "required": ["url", "typename"]
    }
}
```

## QgsProject_addXyzLayer
- **Description**: Adds an XYZ tile layer (e.g., OpenStreetMap, Google Maps).
- **Keywords**: add osm, add google maps, xyz tiles, basemap
- **Schema**:
```json
{
    "name": "QgsProject_addXyzLayer",
    "description": "Adds an XYZ tile layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL with {x}, {y}, {z} placeholders"},
            "layer_name": {"type": "string"}
        },
        "required": ["url", "layer_name"]
    }
}
```
