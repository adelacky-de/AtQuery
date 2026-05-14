# Skill: DataInspection

Guides the agent through inspecting layer metadata, attribute schemas, and feature records with high-fidelity HTML rendering.

## When to Use
- When the user asks about the "columns", "metadata", or "schema" of a layer.
- When the user wants to "see" or "show" data records from a layer.
- When sorting or filtering data in the chat view.

## Process
1. **Field Discovery**: Use `QgsVectorLayer_fields` to understand the schema.
2. **Constraint Validation**: Ensure row limits (clamped to 50) and parameter logic (sort/filter) are correct.
3. **Rendering**: Generate the HTML table using the `get_layer_features_sample` tool.
4. **Verification**: Confirm that the tool output contains the `PRESERVE_AS_HTML` key to trigger the UI interceptor.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll summarize the table as a list to be helpful." | **STRICT NO.** The UI renders HTML better than you can write text. Return ONLY the HTML. |
| "I'll guess the field names based on the layer name." | **NO.** Always call `QgsVectorLayer_fields` first. |
| "I'll make up sample data if the tool fails." | **NO.** If the tool returns an error, report it. Never hallucinate rows. |
| "I'll use `get_layer_metadata` to show column values." | **STRICT NO.** `get_layer_metadata` returns NO row data. For any column/value/example request, ALWAYS use `get_layer_features_sample`. |
| "The user said 'show me records where X', so I'll call selectByExpression." | **STRICT NO.** 'Show me' means DISPLAY. Call `get_layer_features_sample` with the `filter` parameter. `selectByExpression` is for SELECTING features, not displaying them. |
| "The user asked 'what are the columns', so I'll describe them from memory." | **STRICT NO.** Call `get_layer_features_sample` to show real column names and real values from the layer. |

## Verification Gates
- **HTML Presence**: Every data request MUST result in a `PRESERVE_AS_HTML` key.
- **Row Clamp**: Ensure no more than 50 rows are requested to prevent context overflow.

---

### Tool: QgsVectorLayer_fields
- **Description**: Lists all field names and types for a given layer.
- **Schema**:
```json
{
    "name": "QgsVectorLayer_fields",
    "description": "Returns a list of field names for the specified layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    if hasattr(layer, 'fields'):
        result = {"fields": [f.name() for f in layer.fields()]}
    else:
        result = {"error": f"Layer '{layer.name()}' is not a vector layer and has no attribute fields."}
else:
    result = {"error": "Layer not found"}
```

### Tool: QgsVectorLayer_crs
- **Description**: Returns the Coordinate Reference System (CRS) of a layer.
- **Schema**:
```json
{
    "name": "QgsVectorLayer_crs",
    "description": "Returns the Coordinate Reference System (CRS) of a layer.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    result = {"crs": layer.crs().authid(), "description": layer.crs().description()}
else:
    result = {"error": "Layer not found"}
```

### Tool: get_layer_metadata
- **Description**: Returns a comprehensive summary of a layer (CRS, feature count, extent, and geometry type).
- **Schema**:
```json
{
    "name": "get_layer_metadata",
    "description": "Returns ONLY CRS, extent, geometry type, and feature COUNT for a layer. Use ONLY for 'tell me about', 'what is the CRS', 'describe layer' queries. WARNING: This tool returns NO field names and NO data rows. If the user asks for columns, values, fields, records, or example data — do NOT call this tool. Use get_layer_features_sample instead.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
layer = self._resolve_layer(args['layer_name'])
if layer:
    geom_map = {0: "Point", 1: "Line", 2: "Polygon", 3: "Unknown", 4: "NoGeometry"}
    ext = layer.extent()
    result = {
        "name": layer.name(),
        "type": "Vector" if layer.type() == 0 else "Raster",
        "feature_count": layer.featureCount() if layer.type() == 0 else "N/A",
        "crs": layer.crs().authid(),
        "crs_description": layer.crs().description(),
        "extent": {
            "xmin": round(ext.xMinimum(), 6),
            "ymin": round(ext.yMinimum(), 6),
            "xmax": round(ext.xMaximum(), 6),
            "ymax": round(ext.yMaximum(), 6)
        },
        "geometry_type": geom_map.get(layer.geometryType(), "N/A") if layer.type() == 0 else "N/A",
        "note": "This tool returns ONLY metadata. To see actual data values, use get_layer_features_sample."
    }
else:
    result = {"error": "Layer not found"}
```

### Tool: get_layer_features_sample
- **Description**: Returns a sample of features (rows) from the layer's attribute table.
- **Schema**:
```json
{
    "name": "get_layer_features_sample",
    "description": "PRIMARY data viewing tool. Call this for ANY of these requests: 'show me records', 'what are the columns', 'what fields does X have', 'example values', 'what are the values', 'show me data', 'show me top N', 'show sorted by', 'show filtered by'. Returns real attribute table rows as an HTML table. Supports limit (default 5), sort_by, ascending, and filter parameters.",
    "parameters": {
        "type": "object",
        "properties": {
            "layer_name": {"type": "string", "description": "Exact layer name."},
            "limit": {"type": "integer", "description": "Number of rows to return (default 5, max 50)."},
            "sort_by": {"type": "string", "description": "Field name to sort by."},
            "ascending": {"type": "boolean", "description": "Sort ascending (true) or descending (false). Default true."},
            "filter": {"type": "string", "description": "Optional QGIS filter expression e.g. \"NAME_EN\" LIKE '%Central%'."}
        },
        "required": ["layer_name"]
    }
}
```
- **Implementation**:
```python
from qgis.core import QgsFeatureRequest
layer = self._resolve_layer(args['layer_name'])
if layer:
    if hasattr(layer, 'getFeatures'):
        # Clamp limit between 1 and 50 to prevent crashing local LLMs
        limit = min(max(args.get('limit', 5), 1), 50)
        fields = [f.name() for f in layer.fields()]
        
        req = QgsFeatureRequest()
        req.setLimit(limit)
        
        sort_field = args.get('sort_by')
        if sort_field:
            req.setOrderBy(QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(sort_field, args.get('ascending', True))]))
        
        filter_exp = args.get('filter')
        if filter_exp:
            req.setFilterExpression(filter_exp)
        
        # Build HTML table for premium look and to prevent AI hallucination
        html = '<table border="1" style="border-collapse: collapse; width: 100%; font-size: 11px;">'
        html += '<tr style="background-color: #f2f2f2;">' + "".join([f'<th style="padding: 4px;">{f}</th>' for f in fields]) + '</tr>'
        
        count = 0
        for feat in layer.getFeatures(req):
            html += '<tr>' + "".join([f'<td style="padding: 4px;">{str(feat.attributes()[i])}</td>' for i in range(len(fields))]) + '</tr>'
            count += 1
        html += '</table>'
        
        if count == 0:
            result = {"error": "The layer is empty (0 features)."}
        else:
            result = {"status": "success", "PRESERVE_AS_HTML": html}
    else:
        result = {"error": f"Layer '{layer.name()}' has no attribute table (it may be a raster layer)."}
else:
    result = {"error": "Layer not found"}
```
