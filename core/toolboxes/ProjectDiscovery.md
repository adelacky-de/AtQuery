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
    "description": "Returns the name of the currently active/selected layer in the QGIS layer tree. Call this when user says 'this layer', 'current layer', or 'active layer' without naming a specific layer.",
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

### Tool: get_layers_with_selection
- **Description**: Returns all layers that currently have features selected.
- **Schema**:
```json
{
    "name": "get_layers_with_selection",
    "description": "Returns a list of layers that have selected features, along with the selection count. Use this when the user says 'buffer the selected X', 'clip by selected', 'process selected features', or any operation on 'selected [layer type]' where the layer name is not given explicitly.",
    "parameters": {"type": "object", "properties": {}}
}
```
- **Implementation**:
```python
from qgis.core import QgsProject
selected = []
for layer in QgsProject.instance().mapLayers().values():
    if hasattr(layer, 'selectedFeatureCount') and layer.selectedFeatureCount() > 0:
        selected.append({"layer": layer.name(), "selected_count": layer.selectedFeatureCount()})
if selected:
    result = {"layers_with_selection": selected}
else:
    result = {"error": "No layers currently have selected features. Please make a selection first, then retry."}
```
