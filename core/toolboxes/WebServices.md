# Toolbox: WebServices

Adding layers from web-based services (XYZ, WMS, WFS).

### Tool: add_xyz_layer
- **Description**: Adds an XYZ Tile layer (e.g., OpenStreetMap).
- **Schema**:
```json
{
    "name": "add_xyz_layer",
    "description": "Adds an XYZ tile layer to the project.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "XYZ URL."},
            "name": {"type": "string", "description": "Layer name."}
        },
        "required": ["url", "name"]
    }
}
```
- **Implementation**:
```python
from qgis.core import QgsRasterLayer
url = args['url']
# Handle common service names
if url.lower() == 'osm': url = 'type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png'
layer = QgsRasterLayer(url, args['name'], "wms")
if layer.isValid():
    QgsProject.instance().addMapLayer(layer)
    result = {"status": "success"}
else:
    result = {"error": "Invalid URL or service"}
```
