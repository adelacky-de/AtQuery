# ai_brain.py

# 1. The Tool Definitions (Schema)
# This is the standard JSON schema that tells Ollama which QGIS functions are available.
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "QgsProject_mapLayers",
            "description": "Returns a list of all layer names in the current QGIS project. ALWAYS call this first to check available layers before attempting any geospatial operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "refresh": {
                        "type": "boolean",
                        "description": "Set to true to force a refresh of the layer list."
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "QgsVectorLayer_fields",
            "description": "Retreives the field names for a specific layer. You MUST call this if the user asks for attributes, fields, or columns. Example: 'what attributes are in My_Layer?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer (e.g. 'AdminArea_DCD_20230609.gdb_converted'). DO NOT add or remove suffixes."
                    }
                },
                "required": ["layer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "QgsVectorLayer_selectByExpression",
            "description": "Selects features from a vector layer based on an SQL-like query expression and zooms to the selection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer to perform the selection on."
                    },
                    "sql": {
                        "type": "string",
                        "description": "The SQL-like expression to filter features (e.g., \"FIELD_NAME\" = 'Value')."
                    }
                },
                "required": ["layer_name", "sql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_run_joinattributestable",
            "description": "Joins attributes from a secondary layer to a primary layer based on a matching field value. This modifies the primary layer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_layer_name": {
                        "type": "string",
                        "description": "The name of the primary layer to which attributes will be added."
                    },
                    "join_layer_name": {
                        "type": "string",
                        "description": "The name of the secondary layer providing the attributes."
                    },
                    "input_join_field": {
                        "type": "string",
                        "description": "The name of the join field in the primary (input) layer."
                    },
                    "join_layer_field": {
                        "type": "string",
                        "description": "The name of the join field in the secondary (join) layer."
                    },
                    "join_prefix": {
                        "type": "string",
                        "description": "Optional. A prefix to add to the names of the joined fields to avoid collisions."
                    }
                },
                "required": ["input_layer_name", "join_layer_name", "input_join_field", "join_layer_field"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_run_native_buffer",
            "description": "Creates a buffer zone around all features in a layer. This creates a polygon layer with buffered geometries. Use this for distance-based buffer operations (e.g., '500m buffer', '10km buffer').",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer to buffer."
                    },
                    "distance": {
                        "type": "number",
                        "description": "Buffer distance in map units (meters for most projections)."
                    },
                    "output_layer_name": {
                        "type": "string",
                        "description": "Optional. Name for the output buffer layer. If not provided, will be named '{layer_name}_buffer_{distance}m'."
                    }
                },
                "required": ["layer_name", "distance"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "QgsVectorLayer_createMemoryLayer",
            "description": "Creates a memory layer (bbox) from a specified extent. The extent can be '@map_extent' for current view or specific coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The name for the new memory layer."
                    },
                    "extent": {
                        "type": "string",
                        "description": "The extent to use. Use '@map_extent' for current visible extent, or provide coordinates as 'xmin,ymin,xmax,ymax'."
                    }
                },
                "required": ["layer_name", "extent"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "QgsApplication_processingRegistry_algorithms",
            "description": "Searches for geoprocessing algorithms by keywords. Use this when the user asks for a complex operation and you don't know the exact algorithm ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The keyword to search for (e.g., 'slope', 'centroid', 'intersection')."
                    }
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_algorithmHelp",
            "description": "Returns the help description and parameter requirements for a specific QGIS algorithm ID. ALWAYS call this before processing_run if you are unsure about the parameter names or types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "algorithm_id": {
                        "type": "string",
                        "description": "The ID of the algorithm (e.g., 'native:slope', 'qgis:intersection')."
                    }
                },
                "required": ["algorithm_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_run",
            "description": "Executes a specified QGIS geoprocessing algorithm with a dictionary of parameters. This is the most powerful tool for complex operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "algorithm_id": {
                        "type": "string",
                        "description": "The ID of the algorithm to run."
                    },
                    "parameters": {
                        "type": "object",
                        "description": "A dictionary of parameters for the algorithm. Use 'memory:' as the value for 'OUTPUT' to create temporary layers."
                    }
                },
                "required": ["algorithm_id", "parameters"]
            }
        }
    }
]

# 2. The System Instruction (The AI's Personality and Rules)
SYSTEM_PROMPT = """
You are a technical QGIS machine. You have NO personality. You only retrieve data using tools.

WORKFLOW:
1. If you don't know the layers, call `QgsProject_mapLayers`.
2. If you see a layer name in history, call `QgsVectorLayer_fields` to inspect it.
3. If you have the fields, call `QgsVectorLayer_selectByExpression` to filter/count if needed.

RULES:
- ONLY TOOLS: You are FORBIDDEN from answering with text if you haven't called a tool this turn.
- NO REFUSALS: NEVER say "I don't know". If you see a name like "AdminArea", USE IT.
- NO CHAT: NO "Here is what I found". Just output the tool call or the final fact.
- TERMINATION: Stop calling tools once you have data. Your final sentence MUST list the specific names or counts found.

EXAMPLES:
- Find Layers: {"tool_calls": [{"function": {"name": "QgsProject_mapLayers", "arguments": {}}}]}
- Result: "The layers are: LayerA, LayerB"
"""


def get_tools():
    """Returns the tool definitions for the Ollama API call."""
    return TOOLS_SCHEMA

def get_system_prompt():
    """Returns the system instruction for the Ollama API call."""
    return SYSTEM_PROMPT