# RasterAnalysis Toolbox
Keywords: slope, hillshade, aspect, raster, dem, elevation, calculator

## processing_run_gdal_slope
- **Description**: Calculates slope from a DEM raster.
- **Keywords**: slope, incline, gradient, steepness
- **Schema**:
```json
{
    "name": "processing_run_gdal_slope",
    "description": "Calculates slope from a DEM raster.",
    "parameters": {
        "type": "object",
        "properties": {
            "INPUT": {"type": "string", "description": "Path to DEM raster"},
            "OUTPUT": {"type": "string", "description": "memory: or file path"}
        },
        "required": ["INPUT"]
    }
}
```

## processing_run_gdal_hillshade
- **Description**: Generates hillshade from a DEM raster.
- **Keywords**: hillshade, relief, shadow, topography
- **Schema**:
```json
{
    "name": "processing_run_gdal_hillshade",
    "description": "Generates hillshade from a DEM raster.",
    "parameters": {
        "type": "object",
        "properties": {
            "INPUT": {"type": "string"},
            "Z_FACTOR": {"type": "number", "default": 1},
            "AZIMUTH": {"type": "number", "default": 315},
            "V_ANGLE": {"type": "number", "default": 45}
        },
        "required": ["INPUT"]
    }
}
```

## processing_run_qgis_rastercalculator
- **Description**: Performs pixel-based calculations on rasters.
- **Keywords**: raster calculator, map algebra, ndvi, raster math
- **Schema**:
```json
{
    "name": "processing_run_qgis_rastercalculator",
    "description": "Performs calculations on rasters.",
    "parameters": {
        "type": "object",
        "properties": {
            "EXPRESSION": {"type": "string"},
            "LAYERS": {"type": "array", "items": {"type": "string"}},
            "OUTPUT": {"type": "string", "default": "memory:"}
        },
        "required": ["EXPRESSION", "LAYERS"]
    }
}
```
