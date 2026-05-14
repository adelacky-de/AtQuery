# Skill: LayerStyling

Guides the agent through modifying the visual appearance of layers (Color, Transparency) and canvas navigation (Zooming).

## When to Use
- When the user wants to change the "look", "color", or "transparency" of a layer.
- When the user needs to "zoom to" or "center on" a specific layer or coordinate.

## Process
1. **Target Identification**: Resolve the layer name.
2. **Property Mutation**: Modify the renderer (for color/transparency) or map settings (for zoom).
3. **UI Synchronization**: Refresh the layer tree and map canvas to reflect changes.
4. **Verification**: Confirm that the change was applied successfully.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll change the color but skip the refresh." | **NO.** If you don't refresh the symbology, the user won't see the change in the legend. |
| "I'll guess the coordinate if not provided." | **NO.** Use `zoom_to_layer` if coordinates are ambiguous. |

## Verification Gates
- **Visual Update**: Every style change must conclude with `refreshLayerSymbology` and `triggerRepaint`.

---

### Tool: set_layer_color
- **Description**: Sets the fill or line color of a vector layer using a HEX color code.
- **Schema**:
```json
{
  "name": "set_layer_color",
  "description": "Sets the fill or line color of a vector layer using a HEX color code.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer to style."},
      "color_hex": {"type": "string", "description": "The HEX color code (e.g., '#FF0000')."}
    },
    "required": ["layer_name", "color_hex"]
  }
}
```
- **Implementation**:
```python
from qgis.PyQt.QtGui import QColor
layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": f"Layer '{args['layer_name']}' not found."}
else:
    try:
        renderer = layer.renderer()
        if renderer:
            symbol = renderer.symbol()
            symbol.setColor(QColor(args['color_hex']))
            layer.triggerRepaint()
            if hasattr(self.iface, 'layerTreeView'):
                self.iface.layerTreeView().refreshLayerSymbology(layer.id())
            result = {"status": "success", "color": args['color_hex']}
        else:
            result = {"error": "Layer has no renderer (may be a raster)."}
    except Exception as e:
        result = {"error": f"Styling failed: {str(e)}"}
```

### Tool: set_layer_transparency
```json
{
  "name": "set_layer_transparency",
  "description": "Sets the opacity/transparency of a layer.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer."},
      "opacity": {"type": "number", "description": "Opacity value from 0 (fully transparent) to 100 (fully opaque)."}
    },
    "required": ["layer_name", "opacity"]
  }
}
```

```python
layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": f"Layer '{args['layer_name']}' not found."}
else:
    try:
        val = float(args['opacity'])
        opacity_val = val / 100.0
        
        # 1. Set global layer opacity
        layer.setOpacity(opacity_val)
        
        # 2. Force UI and Map canvas to update immediately
        layer.triggerRepaint()
        layer.styleChanged.emit()
        
        if hasattr(self.iface, 'layerTreeView'):
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
            
        self.iface.mapCanvas().refresh()
        
        result = {"status": "success", "message": f"Opacity of '{layer.name()}' set to {val}%"}
    except Exception as e:
        result = {"error": f"Invalid opacity value: {str(e)}"}
```

### Tool: zoom_to_layer
```json
{
  "name": "zoom_to_layer",
  "description": "Zooms the map canvas to the extent of a specific layer.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer to zoom to."}
    },
    "required": ["layer_name"]
  }
}
```

```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    self.iface.mapCanvas().setExtent(layer.extent())
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "message": f"Map zoomed to '{layer.name()}'"}
else:
    result = {"error": "Layer not found"}
```

### Tool: zoom_to_coordinate
```json
{
  "name": "zoom_to_coordinate",
  "description": "Pans and zooms the map canvas to a specific X and Y coordinate.",
  "parameters": {
    "type": "object",
    "properties": {
      "x": {"type": "number", "description": "X coordinate (Longitude or Easting)."},
      "y": {"type": "number", "description": "Y coordinate (Latitude or Northing)."},
      "scale": {"type": "number", "description": "Optional zoom scale (e.g., 10000). Default is 10000."}
    },
    "required": ["x", "y"]
  }
}
```

```python
from qgis.core import QgsPointXY
x = float(args['x'])
y = float(args['y'])
scale = float(args.get('scale', 10000))
center = QgsPointXY(x, y)
self.iface.mapCanvas().setCenter(center)
self.iface.mapCanvas().zoomScale(scale)
self.iface.mapCanvas().refresh()
result = {"status": "success", "message": f"Zoomed to {x}, {y} at scale {scale}"}
```

### Tool: set_layer_visibility
```json
{
  "name": "set_layer_visibility",
  "description": "Shows or hides a layer in the QGIS layer tree (legend). Use this for 'hide', 'show', 'turn off', 'turn on' a layer.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer to show or hide."},
      "visible": {"type": "boolean", "description": "true to show the layer, false to hide it."}
    },
    "required": ["layer_name", "visible"]
  }
}
```

```python
from qgis.core import QgsProject
layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": f"Layer '{args['layer_name']}' not found."}
else:
    visible = bool(args['visible'])
    root = QgsProject.instance().layerTreeRoot()
    node = root.findLayer(layer.id())
    if node:
        node.setItemVisibilityChecked(visible)
        self.iface.mapCanvas().refresh()
        state = "visible" if visible else "hidden"
        result = {"status": "success", "message": f"Layer '{layer.name()}' is now {state}."}
    else:
        result = {"error": "Layer node not found in tree."}
```

### Tool: remove_layer
```json
{
  "name": "remove_layer",
  "description": "Removes a layer from the QGIS project and map canvas. Use for 'remove', 'delete', or 'close' a layer.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer to remove."}
    },
    "required": ["layer_name"]
  }
}
```

```python
from qgis.core import QgsProject
layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": f"Layer '{args['layer_name']}' not found."}
else:
    name = layer.name()
    QgsProject.instance().removeMapLayer(layer.id())
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "message": f"Layer '{name}' has been removed from the project."}
```

### Tool: zoom_to_full_extent
```json
{
  "name": "zoom_to_full_extent",
  "description": "Zooms the map canvas out to show all loaded layers (full project extent). Use for 'zoom to all', 'zoom out', 'see everything'.",
  "parameters": {
    "type": "object",
    "properties": {}
  }
}
```

```python
self.iface.mapCanvas().zoomToFullExtent()
self.iface.mapCanvas().refresh()
result = {"status": "success", "message": "Zoomed to full project extent."}
```
