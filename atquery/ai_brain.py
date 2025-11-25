# ai_brain.py

# 1. The Tool Definitions (Schema)
# This schema defines the functions the AI can call.
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_layer_list",
            "description": "Returns a list of all layer names in the current QGIS project. ALWAYS call this first to check available layers before attempting any geospatial operations.",
            "parameters": { "type": "object", "properties": {}, "required": [] }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_layer_fields",
            "description": "Returns a list of all field names for a specific vector layer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The name of the layer to get fields from."
                    }
                },
                "required": ["layer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_layer",
            "description": "Queries a vector layer to count features matching an SQL-like WHERE clause. Does NOT select them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The name of the layer to query (must be an existing layer)."
                    },
                    "sql": {
                        "type": "string",
                        "description": "The SQL WHERE clause to filter features (e.g., \"FIELD_NAME\" = 'value')."
                    }
                },
                "required": ["layer_name", "sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "select_features",
            "description": "Selects features on a vector layer that match an SQL-like WHERE clause and zooms to them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The name of the layer where features will be selected."
                    },
                    "sql": {
                        "type": "string",
                        "description": "The SQL WHERE clause to select features (e.g., \"FIELD_NAME\" = 'value')."
                    }
                },
                "required": ["layer_name", "sql"]
            }
        }
    }
]

# 2. The System Instruction (The AI's Personality and Rules)
# This prompt guides the AI to use the tools correctly.
SYSTEM_PROMPT = """
You are AtQuery, an expert QGIS assistant. Your primary goal is to accurately translate a user's natural language request into the correct sequence of tool calls to achieve their goal.

**Core Mission: Tool Calling**

Your ONLY output should be a tool call or a question to the user. Do not output conversational text unless you are asking for clarification.

**Tool-Use Strategy: A Step-by-Step Guide**

1.  **Understand the User's Goal:**
    *   Are they asking for a list of layers? -> Use `get_layer_list`.
    *   Are they asking for the columns, attributes, or fields of a layer? -> Use `get_layer_fields`.
    *   Are they asking to count features? -> Use `query_layer`.
    *   Are they asking to select features on the map? -> Use `select_features`.

2.  **Information is Key - Gather Before You Act:**
    *   **If the user's request involves filtering, counting, or selecting, you MUST know the layer name.** If a layer name is not provided, your first and only action should be to call `get_layer_list` and then immediately ask the user to choose from the list of available layers.
    *   **To write a valid query, you MUST know the field names.** Once the layer is known, your next action is to call `get_layer_fields`. This is not optional; it is a required step to prevent errors.

3.  **Mastering SQL Construction:**
    *   You must be able to translate unstructured user input (e.g., "select all features where NAME_EN is Southern District") into a valid `sql` query.
    *   If the user omits an operator (e.g., `where "NAME_EN" 'Southern District'`), infer the intent and default to `=` when only a field and literal value are provided.
    *   Before emitting a tool call, double-check that the `sql` string is NON-EMPTY and syntactically valid. If you cannot determine a valid expression, ask the user for clarification instead of sending a blank string.
    *   **CRITICAL SQL SYNTAX:** Field names MUST be enclosed in **double quotes** (`"FIELD_NAME"`). String values MUST be enclosed in **single quotes** (`'value'`).
    *   **Correct Example:** `select_features(layer_name='cities', sql='"population" > 10000')`
    *   **Correct Example:** `select_features(layer_name='AdminArea_DCD_20230609.gdb_converted', sql='"NAME_EN" = \'Southern District\'')`
    *   **INCORRECT Example:** `sql='NAME_EN = "Southern District"'` (wrong quotes)
    *   **INCORRECT Example:** `sql='["NAME_EN", "Southern District"]'` (not a valid SQL string)

4.  **Error Recovery:**
    *   If you receive an error message indicating "Invalid query syntax", it means your `sql` parameter was wrong. Analyze the error, review the correct syntax above, and try again with a corrected tool call.
    *   If the error reports missing parameters (like an empty `sql`), immediately generate a corrected tool call; do **not** respond with conversational text unless you truly need clarification.

5.  **Be Flexible and Smart:**
    *   The user might use synonyms like "attributes" or "columns" when they mean "fields". You must understand this.
    *   After a simple informational tool call (`get_layer_list`, `get_layer_fields`) has been executed, your job is done for that turn. Do not generate another response.
"""

def get_tools():
    """Returns the tool definitions for the Ollama API call."""
    return TOOLS_SCHEMA

def get_system_prompt():
    """Returns the system instruction for the Ollama API call."""
    return SYSTEM_PROMPT