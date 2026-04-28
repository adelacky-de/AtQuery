# Toolbox: ProjectDiscovery

Basic tools for exploring the current QGIS project state and map metadata.

### Tool: QgsProject_mapLayers
- **Description**: Returns a list of all layer names in the current project.
- **Schema**:
```json
{
    "name": "QgsProject_mapLayers",
    "description": "Lists all layer names in the current QGIS project.",
    "parameters": {
        "type": "object",
        "properties": {}
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
### Tool: get_active_layer
- **Description**: Returns the name and type of the currently selected (active) layer in QGIS.
- **Schema**:
```json
{
    "name": "get_active_layer",
    "description": "Returns the name of the currently active/selected layer in the QGIS layer tree.",
    "parameters": {"type": "object", "properties": {}}
}
```
- **Implementation**:
```python
layer = self.iface.activeLayer()
if layer:
    result = {"name": layer.name(), "type": "vector" if layer.type() == 0 else "raster"}
else:
    result = {"error": "No active layer selected."}
```
