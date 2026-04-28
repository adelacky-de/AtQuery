# Toolbox: ProjectDiscovery

Basic tools for exploring the current QGIS project state and map metadata.

### Tool: QgsProject_mapLayers
- **Description**: Returns a list of all layer names in the current project.
- **Keywords**: list layers, what layers, show project data, map layers
- **Schema**:
```json
{
    "name": "QgsProject_mapLayers",
    "description": "Lists all layer names in the current QGIS project.",
    "parameters": {
        "type": "object",
        "properties": {
            "refresh": {"type": "boolean", "description": "Force refresh metadata."}
        }
    }
}
```
- **Implementation**:
```python
layers = [l.name() for l in QgsProject.instance().mapLayers().values()]
result = {"layers": layers, "count": len(layers)}
```

### Tool: QgsMapCanvas_extent
- **Description**: Returns the bounding box of the current map view.
- **Keywords**: current view, extent, bbox, where am i looking
- **Schema**:
```json
{
    "name": "QgsMapCanvas_extent",
    "description": "Returns the bounding box (xmin, ymin, xmax, ymax) of the current map view.",
    "parameters": {"type": "object", "properties": {}}
}
```
- **Implementation**:
```python
ext = self.iface.mapCanvas().extent()
result = {"xmin": ext.xMinimum(), "ymin": ext.yMinimum(), "xmax": ext.xMaximum(), "ymax": ext.yMaximum()}
```
