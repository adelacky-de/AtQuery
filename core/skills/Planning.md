# Skill: AtQuery-Planning

Guides the local LLM through analyzing GIS requests and mapping them to QGIS toolboxes.

## Process
1. **Layer Resolution**: Identify which layers are needed. If ambiguous, plan to call `get_active_layer` or ask for clarification.
2. **Toolbox Mapping**: Match keywords (e.g., "slope", "buffer") to the correct toolbox (RasterAnalysis, VectorProcessing).
3. **Spatial logic**: If the user asks for "points in polygon", plan to use `SelectionTools` with spatial predicates.
4. **Data Sampling**: Plan to use `get_layer_features_sample` if you need to know field names or value formats before running complex queries.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll guess the layer name." | **NO.** If the name doesn't exist, list all layers first. |
| "I'll assume it's a vector layer." | **NO.** Check if the operation is valid for raster vs vector. |

## Verification Gates
- **Capability Check**: Do I have a toolbox loaded that can handle this request?
