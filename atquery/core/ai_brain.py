# ai_brain.py

import os

# 1. The Skill Library (Categorized by Toolbox)
TOOLBOXES = {
    "ProjectDiscovery": [
        {
            "type": "function",
            "function": {
                "name": "QgsProject_mapLayers",
                "description": "Lists all layer names in the current QGIS project. ALWAYS start here.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean", "description": "Force refresh."}
                    }
                }
            },
        },
        {
            "type": "function",
            "function": {
                "name": "QgsProject_extent",
                "description": "Returns the bounding box of the entire project.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    ],
    "DataInspection": [
        {
            "type": "function",
            "function": {
                "name": "QgsVectorLayer_fields",
                "description": "Retrieves field names for a specific layer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string", "description": "Exact layer name."}
                    },
                    "required": ["layer_name"]
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
                        "layer_name": {"type": "string", "description": "Exact layer name."}
                    },
                    "required": ["layer_name"]
                }
            }
        }
    ],
    "SelectionTools": [
        {
            "type": "function",
            "function": {
                "name": "QgsVectorLayer_selectByExpression",
                "description": "Selects features based on an SQL-like query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"},
                        "sql": {"type": "string", "description": "SQL filter e.g. \"field\" = 'value'"}
                    },
                    "required": ["layer_name", "sql"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run_selectbylocation",
                "description": "Spatial selection between layers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_layer_name": {"type": "string"},
                        "predicate": {"type": "string", "description": "intersect, contains, etc."},
                        "intersect_layer_name": {"type": "string"}
                    },
                    "required": ["input_layer_name", "predicate", "intersect_layer_name"]
                }
            }
        }
    ],
    "LayerStyling": [
        {
            "type": "function",
            "function": {
                "name": "QgsVectorLayer_setSingleSymbolRenderer",
                "description": "Changes layer color.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"},
                        "color": {"type": "string", "description": "Color name or hex."}
                    },
                    "required": ["layer_name", "color"]
                }
            }
        }
    ],
    "VectorProcessing": [
        {
            "type": "function",
            "function": {
                "name": "processing_run_native_buffer",
                "description": "Creates a buffer zone around features.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"},
                        "distance": {"type": "number"},
                        "output_layer_name": {"type": "string"}
                    },
                    "required": ["layer_name", "distance"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run_reprojectlayer",
                "description": "Reprojects a layer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"},
                        "target_crs": {"type": "string"}
                    },
                    "required": ["layer_name", "target_crs"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run_native_clip",
                "description": "Clips a layer using another layer's geometry.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_layer": {"type": "string"},
                        "overlay_layer": {"type": "string"},
                        "output": {"type": "string", "description": "memory: or file path"}
                    },
                    "required": ["input_layer", "overlay_layer"]
                }
            }
        }
    ],
    "RasterAnalysis": [
        {
            "type": "function",
            "function": {
                "name": "processing_run_gdal_slope",
                "description": "Calculates slope from a DEM raster.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "INPUT": {"type": "string", "description": "Path to DEM raster"},
                        "OUTPUT": {"type": "string", "description": "memory: or file path"}
                    },
                    "required": ["INPUT"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run_gdal_hillshade",
                "description": "Generates hillshade from a DEM raster.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "INPUT": {"type": "string"},
                        "Z_FACTOR": {"type": "number", "default": 1},
                        "AZIMUTH": {"type": "number", "default": 315},
                        "V_ANGLE": {"type": "number", "default": 45}
                    },
                    "required": ["INPUT"]
                }
            }
        }
    ],
    "GeometryRefinement": [
        {
            "type": "function",
            "function": {
                "name": "processing_run_native_centroids",
                "description": "Calculates the centroid for each feature in a layer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "INPUT": {"type": "string", "description": "Layer name"},
                        "OUTPUT": {"type": "string", "default": "memory:"}
                    },
                    "required": ["INPUT"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run_native_dissolve",
                "description": "Merges features based on a field or all features.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "INPUT": {"type": "string"},
                        "FIELD": {"type": "string", "description": "Optional field to dissolve by"}
                    },
                    "required": ["INPUT"]
                }
            }
        }
    ],
    "LayerEditing": [
        {
            "type": "function",
            "function": {
                "name": "QgsVectorLayer_startEditing",
                "description": "Starts an editing session for the specified layer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"}
                    },
                    "required": ["layer_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "QgsVectorLayer_commitChanges",
                "description": "Saves all changes made during the editing session.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "layer_name": {"type": "string"}
                    },
                    "required": ["layer_name"]
                }
            }
        }
    ],
    "AdvancedAlgorithms": [
        {
            "type": "function",
            "function": {
                "name": "QgsApplication_processingRegistry_algorithms",
                "description": "Searches for complex algorithms.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string"}
                    },
                    "required": ["search_term"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "processing_run",
                "description": "Runs any QGIS algorithm.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "algorithm_id": {"type": "string"},
                        "parameters": {"type": "object"}
                    },
                    "required": ["algorithm_id", "parameters"]
                }
            }
        }
    ]
}

# 2. Meta-Tools for Skilling (The Toolbox Catalog)
CATALOG_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_toolbox_catalog",
            "description": "Lists all available Toolboxes (categories) and their purposes. Use this to find which skills to load.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "load_toolbox_skills",
            "description": "Loads all detailed skills (functions) for a specific toolbox category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "toolbox_name": {
                        "type": "string", 
                        "enum": list(TOOLBOXES.keys()),
                        "description": "The category name to load."
                    }
                },
                "required": ["toolbox_name"]
            }
        }
    }
]

# 3. The System Instruction (The Skilling Framework)
BASE_SYSTEM_PROMPT = """
# SKILL HANDBOOK: QGIS AI AGENT

You are an expert QGIS Automation Engineer. You operate using a dynamic **Toolbox** system.

## CORE OPERATIONAL PRINCIPLES
1. **Efficiency First**: To save tokens, you do not see all skills at once. Use the Toolbox system to find what you need.
2. **The Toolbox Workflow**:
    - **Step A: Catalog Lookup**: Call `get_toolbox_catalog` to see the available categories.
    - **Step B: Skill Loading**: Call `load_toolbox_skills` for the category that matches the user's request.
    - **Step C: Execution**: Once the skills are loaded, call the specific skill you need.
3. **Step-by-Step Reasoning**: Before every action, perform a "Thought" step to plan your approach.
4. **JSON Precision**: Your output MUST be a valid JSON object.

## CLARIFICATION & PROACTIVITY
1. **Ambiguity**: If a query is broad (e.g., "what layers"), ask for clarification (e.g., "Would you like the Names, the Count, or the Extent?").
2. **Suggested Queries**: Always provide 2 specific follow-up queries at the end of your natural language response in the format:
   `Suggested Query: 1. [Query] 2. [Query]`
3. **Speed Optimization**: If the user's intent clearly maps to a toolbox you've already used or a core discovery tool, skip the Catalog step and go straight to loading or execution.

## YOUR DYNAMIC TOOLBOXES
- **ProjectDiscovery**: Essential for starting (listing layers, checking extent).
- **DataInspection**: For checking fields and CRS.
- **SelectionTools**: For attribute and spatial queries.
- **LayerStyling**: For changing map appearance.
- **VectorProcessing**: For geoprocessing (buffering, reprojection, clipping).
- **RasterAnalysis**: For terrain and grid-based operations.
- **GeometryRefinement**: For centroids, dissolve, and simplification.
- **LayerEditing**: For manual attribute and geometry modifications.
- **AdvancedAlgorithms**: For complex or custom QGIS algorithms.

## OUTPUT FORMAT
Your response MUST be a single JSON object.

```json
{
  "thought": "I will check the catalog to find the correct toolbox for buffering.",
  "tool_calls": [
    {
      "function": {
        "name": "get_toolbox_catalog",
        "arguments": {}
      }
    }
  ]
}
```

## SAFETY CONSTRAINTS
- Do not attempt to delete files or layers.
- Do not use algorithms from unknown providers.
- If a toolbox or skill is missing, report the error in the 'thought'.
"""

def get_toolbox_skills(toolbox_name):
    """Returns the full schemas for a specific toolbox."""
    return TOOLBOXES.get(toolbox_name, [])

def get_base_tools():
    """Returns the meta-tools for the catalog and loading skills."""
    return CATALOG_TOOLS

def get_system_prompt():
    """Returns the system instruction for the Skilling framework."""
    return BASE_SYSTEM_PROMPT