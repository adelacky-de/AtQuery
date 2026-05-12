# AtQuery Final Test Suite

Use these questions to verify the functional integrity and "harness" discipline of the AtQuery plugin.

## 1. Project Discovery & Metadata
- **Question**: "What layers are currently in my map?"
- **Expected**: Calls `QgsProject_mapLayers`. Returns a clean list.
- **Question**: "Tell me about the GOVT_PRS layer."
- **Expected**: Calls `get_layer_metadata`. Shows CRS, feature count, and extent.

## 2. Data Inspection (HTML Interceptor Test)
- **Question**: "Show me the first 3 records of the DCD layer."
- **Expected**: Calls `get_layer_features_sample`. Renders a raw HTML table. **Crucial**: No infinite loops or text summaries of the table.
- **Question**: "What are the columns and some example values for GOVT_PRS?"
- **Expected**: Calls `get_layer_features_sample`. Renders the table.

## 3. Selection & Attribute Queries
- **Question**: "Select the 5 largest areas in the DCD layer based on SHAPE_Area."
- **Expected**: Calls `select_features_advanced`. Zooms to selection.
- **Question**: "Select all schools in GOVT_PRS where NAME_EN starts with 'A'."
- **Expected**: Calls `QgsVectorLayer_selectByExpression`. Zooms to selection.

## 4. Spatial Analysis (Multi-Tool Chaining)
- **Question**: "Buffer the selected schools by 500 meters."
- **Expected**: Calls `native_buffer`. Creates a new 'Buffered' layer.
- **Question**: "Clip the DCD layer using the current selection in GOVT_PRS."
- **Expected**: Calls `native_clip`. Creates a clipped output.

## 5. Styling & Canvas Control
- **Question**: "Change the color of the GOVT_PRS layer to red."
- **Expected**: Calls `set_layer_color`. Legend icon updates immediately.
- **Question**: "Set the transparency of the DCD layer to 50%."
- **Expected**: Calls `set_layer_transparency`. Layer becomes semi-transparent on canvas.
- **Question**: "Zoom to the extent of the DCD layer."
- **Expected**: Calls `zoom_to_layer`.

## 6. Raster Analysis (Terrain Tools)
- **Question**: "Calculate the slope of the elevation layer."
- **Expected**: Calls `gdal_slope`. Checks stats to ensure it's not a flat raster.
- **Question**: "Generate a hillshade for the DEM."
- **Expected**: Calls `gdal_hillshade`.

## 7. Harness & Edge Case Validation
- **Question**: "Show me records for the 'admin' layer." (Assumes name is partial/ambiguous)
- **Expected**: Triggers the **Ambiguity Card** (⚡ Force Match / 🔍 Search & Learn).
- **Question**: "Do something with a layer that doesn't exist."
- **Expected**: Gracefully errors or lists available layers.
- **Question**: "Select all features where SHAPE_Area > 1000000" (Repeatedly)
- **Expected**: **Loop Prevention Check**. The AI should stop after one successful selection turn.
