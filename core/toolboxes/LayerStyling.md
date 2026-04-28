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
    layer.setOpacity(args['opacity'] / 100.0)
    layer.triggerRepaint()
    result = {"status": "success", "message": f"Opacity of '{layer.name()}' set to {args['opacity']}%"}
```
