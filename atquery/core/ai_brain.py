import os
import json
import re

# --- Helper functions to load tools from MD files ---

def _get_base_dir():
    return os.path.dirname(__file__)

def _load_tools_from_md(toolbox_name):
    """Parses tool schemas from the corresponding toolbox MD file."""
    path = os.path.join(_get_base_dir(), 'toolboxes', f"{toolbox_name}.md")
    if not os.path.exists(path):
        return []
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Extract JSON blocks
    schemas = []
    matches = re.finditer(r'```json\n(.*?)\n```', content, re.DOTALL)
    for match in matches:
        try:
            tool_schema = json.loads(match.group(1))
            schemas.append({"type": "function", "function": tool_schema})
        except:
            continue
    return schemas

def _load_catalog_from_md():
    """Parses the toolbox catalog (Master Index) from toolbox.md."""
    path = os.path.join(_get_base_dir(), 'toolbox.md')
    if not os.path.exists(path):
        # Fallback to hardcoded list if file is missing (to prevent boot loops)
        return {
            "ProjectDiscovery": {"keywords": ["layers", "extent"]},
            "DataInspection": {"keywords": ["fields", "crs"]},
            "SelectionTools": {"keywords": ["select", "filter"]},
            "VectorProcessing": {"keywords": ["buffer", "clip"]},
            "RasterAnalysis": {"keywords": ["slope", "hillshade"]},
            "WebServices": {"keywords": ["wms", "wfs"]},
            "TerrainAnalysis": {"keywords": ["tin", "contours"]}
        }
    
    with open(path, 'r') as f:
        content = f.read()
    
    catalog = {}
    # Parse table rows: | **Name** | Keywords | Description |
    rows = re.findall(r'\|\s*\*\*(\w+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|', content)
    for name, keywords, desc in rows:
        catalog[name.strip()] = {
            "keywords": [k.strip() for k in keywords.split(',')],
            "description": desc.strip()
        }
    return catalog

# --- Core API ---

def get_toolbox_skills(toolbox_name):
    """Returns the full schemas for a specific toolbox, loaded from MD."""
    return _load_tools_from_md(toolbox_name)

def get_base_tools():
    """
    Returns the base tools available at the start of every turn.
    Now includes QgsProject_mapLayers for immediate context.
    """
    catalog = _load_catalog_from_md()
    
    base_tools = [
        {
            "type": "function",
            "function": {
                "name": "get_toolbox_catalog",
                "description": "Lists all available Toolboxes, their keywords, and descriptions. Use this to find which skills to load.",
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
                            "enum": list(catalog.keys()),
                            "description": "The category name to load."
                        }
                    },
                    "required": ["toolbox_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "QgsProject_mapLayers",
                "description": "Lists all layer names in the current QGIS project. Use this for immediate context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "refresh": {"type": "boolean", "description": "Force refresh."}
                    }
                }
            }
        }
    ]
    return base_tools

# --- The System Instruction (The Skilling Framework) ---

BASE_SYSTEM_PROMPT = """
You are "AtQuery", an expert GIS AI agent for QGIS. 
You are a "Dictionary-based" assistant. You MUST use tools to perform actions.

MANDATORY WORKFLOW:
1. If the user query is clear, identify the relevant toolbox using keywords from `get_toolbox_catalog`.
2. Load the toolbox skills using `load_toolbox_skills`.
3. Execute the specific tool.

PROACTIVE FALLBACK & CLARIFICATION:
- If you are uncertain about the user's intent, DO NOT guess a tool. Instead, respond with:
  "Do you want to [action]?" (e.g. "Do you want to buffer the layer?")
- If the user responds with "Y", "YES", or repeats the query, proceed with loading and executing the tool.
- If the user is completely vague, use `get_toolbox_catalog` to show available categories and ask for clarification.

RESPONSE FORMAT:
- You MUST output valid JSON.
- Include a "content" field for your textual response.
- Include a "suggested_queries" array with 2-3 relevant follow-up questions.
- If calling a tool, include the "tool_calls" array.

EXAMPLE OUTPUT:
{
  "content": "I have listed the layers in your project. Would you like to buffer one of them?",
  "suggested_queries": ["Buffer AdminArea_DCD", "List fields for POIs"],
  "tool_calls": [...]
}

Output ONLY the JSON object. No conversational filler outside the JSON.
"""

def get_system_prompt():
    """Returns the system instruction for the Skilling framework."""
    return BASE_SYSTEM_PROMPT