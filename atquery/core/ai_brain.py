import os
import json
import re

# --- Global Skill Registry (Caches implementation code) ---
SKILL_IMPLEMENTATIONS = {}

def _get_base_dir():
    return os.path.dirname(__file__)

def _load_tools_from_md(toolbox_name):
    """
    Parses tool schemas AND implementations from the toolbox MD file.
    Updates the global SKILL_IMPLEMENTATIONS cache.
    """
    path = os.path.join(_get_base_dir(), 'toolboxes', f"{toolbox_name}.md")
    if not os.path.exists(path): return []
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content by "### Tool:" to process each tool independently
    sections = re.split(r'### Tool:', content)[1:]
    schemas = []
    
    for section in sections:
        # Extract Schema JSON
        schema_match = re.search(r'```json\n(.*?)\n```', section, re.DOTALL)
        # Extract Implementation Python
        impl_match = re.search(r'```python\n(.*?)\n```', section, re.DOTALL)
        
        if schema_match:
            try:
                tool_schema = json.loads(schema_match.group(1))
                tool_name = tool_schema.get("name")
                schemas.append({"type": "function", "function": tool_schema})
                
                # Cache the implementation if found
                if impl_match and tool_name:
                    SKILL_IMPLEMENTATIONS[tool_name] = impl_match.group(1).strip()
            except: continue
            
    return schemas

def _load_catalog_from_md():
    path = os.path.join(_get_base_dir(), 'toolbox.md')
    if not os.path.exists(path): return {}
    with open(path, 'r', encoding='utf-8') as f: content = f.read()
    catalog = {}
    rows = re.findall(r'\|\s*\*\*(\w+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|', content)
    for name, keywords, desc in rows:
        catalog[name.strip()] = {"keywords": [k.strip() for k in keywords.split(',')], "description": desc.strip()}
    return catalog

def identify_toolboxes(query):
    catalog = _load_catalog_from_md()
    query_clean = query.lower()
    matches = []
    for name, info in catalog.items():
        for kw in info['keywords']:
            if re.search(rf'\b{re.escape(kw.lower())}\b', query_clean):
                matches.append(name)
                break
    return list(set(matches))

# --- Core API ---

def get_toolbox_skills(toolbox_name):
    return _load_tools_from_md(toolbox_name)

def get_implementation(tool_name):
    """Returns the cached Python code for a tool."""
    return SKILL_IMPLEMENTATIONS.get(tool_name)

def get_base_tools():
    catalog = _load_catalog_from_md()
    # We load ProjectDiscovery immediately as base skills
    base_tools = _load_tools_from_md("ProjectDiscovery")
    
    # Add the loader tool
    base_tools.append({
        "type": "function",
        "function": {
            "name": "load_toolbox_skills",
            "description": f"Load advanced tools. Options: {', '.join(catalog.keys())}",
            "parameters": {
                "type": "object",
                "properties": {
                    "toolbox_name": {"type": "string", "enum": list(catalog.keys())}
                },
                "required": ["toolbox_name"]
            }
        }
    })
    return base_tools

BASE_SYSTEM_PROMPT = """
You are "AtQuery", a QGIS AI Agent. 
You operate using a Dynamic Skill Library.

MANDATORY RULES:
1. ALWAYS use tools for GIS actions. Output ONLY valid JSON.
2. If you see a query matching keywords for a toolbox, LOAD it immediately and call the tool in the same turn.
3. DO NOT ask "Do you want to proceed?" if the command is specific. Just execute.
4. If a tool call fails, analyze the error and try a different parameter or tool.

JSON FORMAT:
{
  "content": "Description of action",
  "tool_calls": [...],
  "suggested_queries": ["Follow up 1", "Follow up 2"]
}
"""

def get_system_prompt():
    return BASE_SYSTEM_PROMPT