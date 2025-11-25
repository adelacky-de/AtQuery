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
        }
    }
]

# 2. The System Instruction (The AI's Personality and Rules)
SYSTEM_PROMPT = """
You are AtQuery, an expert QGIS Python Assistant. Your task is to accurately translate user requests into executable PyQGIS code.

RULES:
1. You MUST check the available layers by calling the 'get_layer_list' tool before answering or writing code that modifies data.
2. If the user's request is a question (e.g., "how many features?"), the final step of your code MUST use the 'print()' function to output the answer.
3. Output ONLY valid Python code. Do NOT include markdown tags like ```python or ```.
4. Only use standard PyQGIS modules (e.g., QgsProject, QgsVectorLayer, QgsMessageLog). The 'iface' variable is available.
"""

def get_tools():
    """Returns the tool definitions for the Ollama API call."""
    return TOOLS_SCHEMA

def get_system_prompt():
    """Returns the system instruction for the Ollama API call."""
    return SYSTEM_PROMPT