# TerrainAnalysis Toolbox
Keywords: tin, contours, isolines, interpolation, 3d, terrain

## processing_run_qgis_tininterpolation
- **Description**: Creates a TIN (Triangulated Irregular Network) from vector points.
- **Keywords**: tin, triangulate, create terrain, point interpolation
- **Schema**:
```json
{
    "name": "processing_run_qgis_tininterpolation",
    "description": "Creates a TIN interpolation.",
    "parameters": {
        "type": "object",
        "properties": {
            "INTERPOLATION_DATA": {"type": "string", "description": "Layer and field config"},
            "METHOD": {"type": "number", "default": 0},
            "EXTENT": {"type": "string"},
            "PIXEL_SIZE": {"type": "number", "default": 0.1},
            "OUTPUT": {"type": "string", "default": "memory:"}
        },
        "required": ["INTERPOLATION_DATA", "EXTENT"]
    }
}
```

## processing_run_gdal_contour
- **Description**: Generates contour lines from a DEM raster.
- **Keywords**: contours, isolines, topo lines, elevation lines
- **Schema**:
```json
{
    "name": "processing_run_gdal_contour",
    "description": "Generates contours from a raster.",
    "parameters": {
        "type": "object",
        "properties": {
            "INPUT": {"type": "string"},
            "INTERVAL": {"type": "number", "default": 10},
            "FIELD_NAME": {"type": "string", "default": "ELEV"},
            "OUTPUT": {"type": "string", "default": "memory:"}
        },
        "required": ["INPUT"]
    }
}
```
