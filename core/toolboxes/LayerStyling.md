# LayerStyling Toolbox

This toolbox provides skills to modify the visual appearance of layers in QGIS.

### Tool: set_layer_color
```json
{
  "name": "set_layer_color",
  "description": "Sets the fill or line color of a vector layer using a HEX color code.",
  "parameters": {
    "type": "object",
    "properties": {
      "layer_name": {"type": "string", "description": "The name of the layer to style."},
      "color_hex": {"type": "string", "description": "The HEX color code (e.g., '#FF0000' for red)."}
    },
    "required": ["layer_name", "color_hex"]
  }
}
```

```python
from qgis.PyQt.QtGui import QColor

layer = self._resolve_layer(args['layer_name'])
if not layer:
    result = {"error": f"Layer '{args['layer_name']}' not found."}
else:
    renderer = layer.renderer()
    symbol = renderer.symbol()
    symbol.setColor(QColor(args['color_hex']))
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())
    result = {"status": "success", "message": f"Color of '{layer.name()}' set to {args['color_hex']}"}
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
        
        # 2. Force the renderer to acknowledge it if it's a vector layer
        if hasattr(layer, 'renderer'):
            renderer = layer.renderer()
            if renderer:
                renderer.setOpacity(opacity_val)
                
        # 3. Force UI and Map canvas to update immediately
        layer.triggerRepaint()
        layer.styleChanged.emit()
        
        if hasattr(iface, 'layerTreeView'):
            iface.layerTreeView().refreshLayerSymbology(layer.id())
            
        iface.mapCanvas().refresh()
        
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
