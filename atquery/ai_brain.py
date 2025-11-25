# ai_brain.py

# 1. The Tool Definitions (Schema)
# This is the standard JSON schema that tells Ollama which QGIS functions are available.
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_layer_list",
            "description": "Returns a list of all layer names in the current QGIS project. ALWAYS call this first to check available layers before attempting any geospatial operations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_layer_details",
            "description": "Returns details (name and fields) for a specific layer. Use this after get_layer_list if you need to know the available fields for a layer before constructing a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The name of the layer to get details for."
                    }
                },
                "required": ["layer_name"]
            }
        }
    }
]

# 2. The System Instruction (The AI's Personality and Rules)
SYSTEM_PROMPT = """
You are AtQuery, an autonomous QGIS Python Agent.
Your ONLY goal is to execute PyQGIS code to fulfill the user's request.

RULES:
1. FIRST, call 'get_layer_list' to find available layers.
2. IF the user's request involves a specific layer and you need to confirm its exact name or available fields, call 'get_layer_details' with the most likely layer name.
3. THEN, write valid PyQGIS code to perform the action.
4. FOR SELECTION/FILTERING: Use `layer.selectByExpression("expression")` to select features on the map.
   - ALWAYS double-quote field names (e.g., `"FIELD_NAME"`).
   - ALWAYS single-quote string values (e.g., `'String Value'`).
   - Use the full, exact layer name identified from 'get_layer_list' or 'get_layer_details' when calling tools like 'query_layer' or 'select_features'.
5. FOR COUNTING: Use `print(layer.featureCount())` or `print(layer.selectedFeatureCount())`.
6. DO NOT explain the code. DO NOT say "Here is the code". Just output the raw code.
7. DO NOT use markdown blocks (```python). Just write the code directly.
8. Only use standard PyQGIS modules (e.g., QgsProject, QgsVectorLayer, QgsMessageLog). The 'iface' variable is available.

Example 1 (Selection):
layer = QgsProject.instance().mapLayersByName('MyLayer')[0]
layer.selectByExpression('"AREA_CODE" = \'STH\'')
print(f"Selected {layer.selectedFeatureCount()} features.")

Example 2 (Counting):
layer = QgsProject.instance().mapLayersByName('MyLayer')[0]
print(layer.featureCount())

Example 3 (Selection with partial layer name and specific condition):
User: Select features in AdminArea where NAME_EN = Southern District
AI Action: Call select_features tool with layer_name='AdminArea_DCD_20230609.gdb_converted' and sql='"NAME_EN" = \'Southern District\''.
"""

def get_tools():
    """Returns the tool definitions for the Ollama API call."""
    return TOOLS_SCHEMA

def get_system_prompt():
    """Returns the system instruction for the Ollama API call."""
    return SYSTEM_PROMPT