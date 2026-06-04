# AtQuery Final Test Suite

Use these questions to verify the functional integrity and "harness" discipline of the AtQuery plugin.
Run against two loaded layers: **DCD** (polygon, district boundaries) and **GOVT_PRS** (point, government premises).

---

## 1. Project Discovery & Metadata
- **Question**: "What layers are currently in my map?"
  - **Expected**: Calls `QgsProject_mapLayers`. Returns a clean list. No hallucinated layer names.
- **Question**: "Tell me about the GOVT_PRS layer."
  - **Expected**: Calls `get_layer_metadata`. Shows CRS, feature count, and extent.
- **Question**: "What is the coordinate system of the DCD layer?"
  - **Expected**: Calls `QgsVectorLayer_crs`. Returns the EPSG code and description.
- **Question**: "What is the current map extent?"
  - **Expected**: Calls `QgsMapCanvas_extent`. Returns xmin/ymin/xmax/ymax.
- **Question**: "What is the active layer?"
  - **Expected**: Calls `get_active_layer`. Returns the currently selected layer name.

---

## 2. Data Inspection (HTML Interceptor Test)
- **Question**: "Show me the first 3 records of the DCD layer."
  - **Expected**: Calls `get_layer_features_sample`. Renders a raw HTML table. **Crucial**: No infinite loops or text summaries of the table.
- **Question**: "What are the columns and some example values for GOVT_PRS?"
  - **Expected**: Calls `get_layer_features_sample`. Renders the table.
- **Question**: "What fields does the DCD layer have?"
  - **Expected**: Calls `QgsVectorLayer_fields`. Returns a list of field names. No table rendered.
- **Question**: "Show me the top 5 largest areas in DCD sorted by SHAPE_Area descending."
  - **Expected**: Calls `get_layer_features_sample` with `sort_by=SHAPE_Area`, `ascending=false`, `limit=5`. Renders HTML table.
- **Question**: "Show me records from GOVT_PRS where NAME_EN contains 'Central'."
  - **Expected**: Calls `get_layer_features_sample` with a filter expression. Renders filtered HTML table.

---

## 3. Selection & Attribute Queries
- **Question**: "Select the 5 largest areas in the DCD layer based on SHAPE_Area."
  - **Expected**: Calls `select_features_advanced`. Zooms to selection. Reports count only — no table.
- **Question**: "Select all schools in GOVT_PRS where NAME_EN starts with 'A'."
  - **Expected**: Calls `QgsVectorLayer_selectByExpression` with `"NAME_EN" LIKE 'A%'`. Zooms to selection.
- **Question**: "Select all features in DCD where SHAPE_Area > 1000000."
  - **Expected**: Calls `QgsVectorLayer_selectByExpression`. Reports count. Does NOT also call `select_features_advanced`.
- **Question**: "Select points in GOVT_PRS that are inside the DCD layer."
  - **Expected**: Calls `processing_select_by_location` with predicate `are within`.
- **Question**: "Clear all selections."
  - **Expected**: Calls `clear_selections`. Repaint confirmed.

---

## 4. Spatial Analysis (Multi-Tool Chaining)
- **Question**: "Buffer the selected schools by 500 meters."
  - **Expected**: Calls `processing_run_native_buffer`. Creates a new `GOVT_PRS_500m_buffer` layer. Reports feature count.
- **Question**: "Clip the DCD layer using the current selection in GOVT_PRS."
  - **Expected**: Calls `processing_run_native_clip`. Creates a `DCD_clipped` layer.
- **Question**: "Extract the selected features from the DCD layer into a new layer."
  - **Expected**: Calls `extract_selected_features`. Creates a new memory layer named `DCD_selection`.
- **Question**: "Find the intersection of DCD and GOVT_PRS."
  - **Expected**: Calls `processing_run_native_intersection`. Creates `DCD_intersected` layer.
- **Question**: "Create centroids for the DCD layer."
  - **Expected**: Calls `processing_run_native_centroids`. Creates `DCD_centroids` point layer.
- **Question**: "Dissolve all features in the DCD layer."
  - **Expected**: Calls `processing_run_native_dissolve`. Creates `DCD_dissolved` layer.
- **Question**: "Reproject the GOVT_PRS layer to WGS84."
  - **Expected**: Calls `processing_run_native_reproject` with `target_crs=EPSG:4326`.

---

## 5. Styling & Canvas Control
- **Question**: "Change the color of the GOVT_PRS layer to red."
  - **Expected**: Calls `set_layer_color` with `#FF0000`. Legend icon updates immediately.
- **Question**: "Set the transparency of the DCD layer to 50%."
  - **Expected**: Calls `set_layer_transparency` with `opacity=50`. Layer becomes semi-transparent on canvas.
- **Question**: "Zoom to the extent of the DCD layer."
  - **Expected**: Calls `zoom_to_layer`. Canvas reframes to DCD extent.
- **Question**: "Make the DCD layer fully opaque again."
  - **Expected**: Calls `set_layer_transparency` with `opacity=100`.

---

## 6. Export Tools
- **Question**: "Export the GOVT_PRS layer as a CSV file."
  - **Expected**: Calls `export_layer_to_file` with `format=CSV`. Reports saved path.
- **Question**: "Save the DCD layer as a GeoJSON."
  - **Expected**: Calls `export_layer_to_file` with `format=GeoJSON`. Reports saved path.
- **Question**: "Save the current map view as a PNG image."
  - **Expected**: Calls `export_map_canvas`. Reports saved path.

---

## 7. Raster Analysis (Terrain Tools)
> ⚠️ Requires a raster/DEM layer loaded in the project. Skip if no raster is present.

- **Question**: "Calculate the slope of the elevation layer."
  - **Expected**: Calls `gdal_slope`. Uses `TEMPORARY_OUTPUT`. Checks stats to ensure min ≠ max. Reports layer name.
- **Question**: "Generate a hillshade for the DEM."
  - **Expected**: Calls `gdal_hillshade`. Checks `isValid()`. Reports layer name.
- **Question**: "Try to run slope on the GOVT_PRS layer." *(negative test)*
  - **Expected**: Gracefully returns `{"error": "Layer '...' is a vector layer. Slope requires a raster DEM."}`.

---

## 8. Harness & Edge Case Validation
- **Question**: "Show me records for the 'admin' layer." *(partial/ambiguous name)*
  - **Expected**: Triggers the **Ambiguity Card** (⚡ Force Match / 🔍 Search & Learn) with clickable layer links.
- **Question**: "Do something with a layer that doesn't exist."
  - **Expected**: Gracefully returns `{"error": "Layer not found"}` and shows the Fallback Card. Does NOT hallucinate a layer.
- **Question**: "Select all features where SHAPE_Area > 1000000" *(sent repeatedly)*
  - **Expected**: **Loop Prevention Check**. After one successful selection, the AI reports the count and STOPS. Circuit breaker fires if called again immediately.
- **Question**: "What is a good buffer distance for schools?" *(no GIS action possible)*
  - **Expected**: Falls through to the Fallback Card. Does NOT fabricate a tool call. Offers ⚡ Force Match or 🔍 Search & Learn.
- **Question**: "Tell me about this layer." *(without naming a layer)*
  - **Expected**: Calls `get_active_layer` first, then `get_layer_metadata` on the result. Does NOT guess a layer name.
- **Question**: "Tell me about GOVT_PRS." *(explicit name, no active layer needed)*
  - **Expected**: Does NOT call `get_active_layer`. Calls `get_layer_metadata` directly with `GOVT_PRS`.
