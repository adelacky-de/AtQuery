# Toolbox: SelectionTools

Tools for spatial and attribute-based selection.

### Tool: QgsVectorLayer_selectByExpression
- **Description**: Selects features in a layer using a SQL-like expression.
- **Keywords**: select, filter, query, where, expression
- **Schema**:
```json
{
    "name": "QgsVectorLayer_selectByExpression",
    "description": "Selects features in a vector layer using a SQL expression.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Layer name."},
            "sql": {"type": "string", "description": "SQL expression (e.g. \"NAME\" = 'Southern District')"}
        },
        "required": ["layer_name", "sql"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    layer.selectByExpression(args['sql'])
    count = layer.selectedFeatureCount()
    layer.triggerRepaint()
    if count > 0: self.iface.mapCanvas().zoomToSelected(layer)
    self.iface.mapCanvas().refresh()
    result = {"status": "success", "count": count}
else:
    result = {"error": "Layer not found"}
```
