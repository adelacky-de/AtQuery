# ai_brain.py

import os

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
            "name": "QgsVectorLayer_setSingleSymbolRenderer",
            "description": "Changes the color of a vector layer to a single specified color. Use this to change layer appearance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer to change the color of."
                    },
                    "color": {
                        "type": "string",
                        "description": "The color to set. Can be a color name (e.g., 'red'), or a hex code (e.g., '#FF0000')."
                    }
                },
                "required": ["layer_name", "color"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "QgsVectorLayer_crs",
            "description": "Returns the Coordinate Reference System (CRS) of a layer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer to get the CRS from."
                    }
                },
                "required": ["layer_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_run_reprojectlayer",
            "description": "Reprojects a layer to a new Coordinate Reference System (CRS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "layer_name": {
                        "type": "string",
                        "description": "The EXACT name of the layer to reproject."
                    },
                    "target_crs": {
                        "type": "string",
                        "description": "The target CRS, e.g., 'EPSG:4326'."
                    },
                    "output_layer_name": {
                        "type": "string",
                        "description": "Optional. Name for the output reprojected layer."
                    }
                },
                "required": ["layer_name", "target_crs"]
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
            "name": "QgsProject_extent",
            "description": "Returns the extent (bounding box) of the entire QGIS project. Use this when the user asks for the overall map extent.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "processing_run_selectbylocation",
            "description": "Selects features from a layer that have a spatial relationship (intersect, contain, overlap) with features from another layer or a geometry. Use this for any spatial query like 'select features in this area' or 'find points inside this polygon'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_layer_name": {
                        "type": "string",
                        "description": "The name of the layer from which to select features."
                    },
                    "predicate": {
                        "type": "string",
                        "description": "The geometric predicate to use. Examples: 'intersect', 'contains', 'overlaps', 'equals', 'crosses', 'disjoint', 'touches', 'within'. Use a list for multiple predicates e.g., ['intersect', 'contains']"
                    },
                    "intersect_layer_name": {
                        "type": "string",
                        "description": "The name of the layer to use for the spatial comparison."
                    }
                },
                "required": ["input_layer_name", "predicate", "intersect_layer_name"]
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
            "description": "Creates a temporary memory layer (e.g., a bounding box polygon) from a specified extent. The extent can be '@map_extent' for the current view or specific coordinates as 'xmin,ymin,xmax,ymax'. This tool is for creating a *new layer* representing an area, not for *getting* the extent of an existing layer or the project.",
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
BASE_SYSTEM_PROMPT = """
You are a QGIS processing engine. Your only purpose is to receive user requests and translate them into QGIS tool calls. You must follow the rules and workflow exactly as described.

**CRITICAL INSTRUCTION: YOUR ENTIRE RESPONSE MUST BE A SINGLE, VALID JSON OBJECT. DO NOT INCLUDE ANY CONVERSATIONAL TEXT, EXPLANATIONS, OR MARKDOWN OUTSIDE OF THE JSON. DO NOT USE `<|python_tag|>`. ANY DEVIATION WILL BE CONSIDERED AN ERROR.**

**WORKFLOW:**

1.  **ALWAYS START HERE:** The first step for any task is to understand the available layers. Call `QgsProject_mapLayers` to get a list of layer names. Do not assume any layers exist.
2.  **INSPECT THE DATA:** Before performing any query or operation on a layer, you MUST know its structure. Call `QgsVectorLayer_fields` to get the attribute fields for any layer you intend to use.
3.  **EXECUTE THE ACTION:** Based on the user's goal and your knowledge of the layer fields, choose the single best tool for the job.
    *   For attribute queries (e.g., `name = 'New York'`), use `QgsVectorLayer_selectByExpression`.
    *   For spatial queries (e.g., `find features inside this polygon`), use `processing_run_selectbylocation`.
    *   For changing layer appearance, use `QgsVectorLayer_setSingleSymbolRenderer`.
    *   For creating buffers, use `processing_run_native_buffer`.
    *   For more complex geoprocessing, search with `QgsApplication_processingRegistry_algorithms`, get help with `processing_algorithmHelp`, and then execute with `processing_run`.

**RULES:**

1.  **JSON ONLY:** Your entire output must be a single, valid JSON object.
2.  **NO CONVERSATION:** Do not respond with conversational text. Do not explain your steps. Your only output should be a valid JSON object containing your tool calls.
3.  **NO `<|python_tag|>`:** Absolutely do not include `<|python_tag|>` or any similar tags in your output.
4.  **LAYER NAMES ARE EXACT:** Use the exact layer names provided by `QgsProject_mapLayers`. Do not guess, hallucinate, or modify layer names. If a layer name from the user does not exist, you must still try to use it.
5.  **SQL QUOTING IS CRITICAL:** When using `QgsVectorLayer_selectByExpression`, field names MUST be in **double quotes** (`"FIELD_NAME"`) and string values MUST be in **single quotes** (`'value'`).
    *   **Correct:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_selectByExpression", "arguments": {"layer_name": "MyLayer", "sql": "\\"status\\" = 'active'"}}}]}`
    *   **Incorrect:** `... "sql": "'status' = 'active'" ...` (wrong field quotes)
    *   **Incorrect:** `... "sql": "\\"status\\" = \\"active\\"" ...` (wrong value quotes)
6.  **ONE GOAL, ONE TOOL:** Do not chain multiple tools together in one response. Choose the single best tool for the immediate task.
7.  **DO NOT HALLUCINATE:** Only use information explicitly provided in the tool schemas or previous tool outputs. Do not invent layer names, field names, or values.
8.  **STRICT TYPE ADHERENCE:** Always match the parameter types defined in the `TOOLS_SCHEMA`.
    *   `QgsProject_mapLayers` `refresh` parameter is a `boolean`. Use `true` or `false` (JSON booleans), not strings.
    *   `QgsVectorLayer_setSingleSymbolRenderer` `color` parameter is a `string`. Provide a color name (e.g., 'red') or hex code (e.g., '#FF0000').
    *   `processing_run_native_buffer` `distance` parameter is a `number`. Provide a number (e.g., `100`), not a string.
    *   `processing_run_selectbylocation` `predicate` parameter is a `string`. Provide a single string (e.g., 'intersects'), not a list.
    *   `QgsVectorLayer_crs` returns a string (e.g., 'EPSG:4326'), not a QgsCoordinateReferenceSystem object.
    *   `processing_run_reprojectlayer` `target_crs` parameter is a `string`. Provide a string (e.g., 'EPSG:3857').
    *   `QgsVectorLayer_createMemoryLayer` `extent` parameter is a `string`. Provide a string (e.g., '@map_extent' or 'xmin,ymin,xmax,ymax').
    *   `processing_algorithmHelp` `algorithm_id` parameter is a `string`.
    *   `processing_run` `parameters` parameter is an `object` (JSON dictionary).

**EXAMPLES:**

*   **User:** "What layers are in my project?"
    **You:** `{"tool_calls": [{"function": {"name": "QgsProject_mapLayers", "arguments": {"refresh": false}}}]}`
*   **User:** "Show me the fields for the 'districts' layer."
    **You:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_fields", "arguments": {"layer_name": "districts"}}}]}`
*   **User:** "Select all districts with a population over 10000."
    **You:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_selectByExpression", "arguments": {"layer_name": "districts", "sql": "\\"population\\" > 10000"}}}]}`
*   **User:** "Find roads that cross the 'districts' layer."
    **You:** `{"tool_calls": [{"function": {"name": "processing_run_selectbylocation", "arguments": {"input_layer_name": "roads", "predicate": "crosses", "intersect_layer_name": "districts"}}}]}`
*   **User:** "Make the 'roads' layer bright red."
    **You:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_setSingleSymbolRenderer", "arguments": {"layer_name": "roads", "color": "red"}}}]}`
*   **User:** "Create a 500-meter buffer around the 'hospitals' layer."
    **You:** `{"tool_calls": [{"function": {"name": "processing_run_native_buffer", "arguments": {"layer_name": "hospitals", "distance": 500}}}]}`
*   **User:** "What is the CRS of the 'roads' layer?"
    **You:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_crs", "arguments": {"layer_name": "roads"}}}]}`
*   **User:** "Reproject 'points_of_interest' to EPSG:3857 and call it 'pois_mercator'."
    **You:** `{"tool_calls": [{"function": {"name": "processing_run_reprojectlayer", "arguments": {"layer_name": "points_of_interest", "target_crs": "EPSG:3857", "output_layer_name": "pois_mercator"}}}]}`
*   **User:** "Create a bounding box layer named 'my_bbox' for the current map extent."
    **You:** `{"tool_calls": [{"function": {"name": "QgsVectorLayer_createMemoryLayer", "arguments": {"layer_name": "my_bbox", "extent": "@map_extent"}}}]}`
*   **User:** "Search for algorithms related to 'clip'."
    **You:** `{"tool_calls": [{"function": {"name": "QgsApplication_processingRegistry_algorithms", "arguments": {"search_term": "clip"}}}]}`
*   **User:** "Get help for 'native:buffer'."
    **You:** `{"tool_calls": [{"function": {"name": "processing_algorithmHelp", "arguments": {"algorithm_id": "native:buffer"}}}]}`
*   **User:** "Run the 'native:union' algorithm on 'layer1' and 'layer2'."
    **You:** `{"tool_calls": [{"function": {"name": "processing_run", "arguments": {"algorithm_id": "native:union", "parameters": {"INPUT": "layer1", "OVERLAY": "layer2", "OUTPUT": "memory:"}}}}]}`
"""


def get_tools():
    """Returns the tool definitions for the Ollama API call."""
    return TOOLS_SCHEMA

def get_system_prompt():
    """
    Returns the system instruction for the Ollama API call.
    """
    return BASE_SYSTEM_PROMPT