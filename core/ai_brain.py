import os
import json
import re

# --- Global Skill Registry (Caches implementation code) ---
SKILL_IMPLEMENTATIONS = {}

# --- Community Toolbox Path ---
_COMMUNITY_TOOLBOX_PATH = os.path.join(os.path.dirname(__file__), 'community_toolbox.json')

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
    """Returns list of matching built-in toolbox names."""
    catalog = _load_catalog_from_md()
    query_clean = query.lower()
    matches = []
    for name, info in catalog.items():
        for kw in info['keywords']:
            if re.search(rf'\b{re.escape(kw.lower())}\b', query_clean):
                matches.append(name)
                break
    return list(set(matches))


def get_available_toolboxes_summary() -> str:
    """
    Returns a human-readable, specific list of all built-in toolboxes
    and their keywords — used in the fallback confirmation dialog.
    """
    catalog = _load_catalog_from_md()
    lines = []
    for name, info in catalog.items():
        kws = ', '.join(info['keywords'][:5])  # Show first 5 keywords
        lines.append(f"• {name}: [{kws}]")
    return '\n'.join(lines)


def load_community_toolbox() -> list:
    """
    Loads tools from community_toolbox.json.
    Returns list of Ollama-compatible tool schemas and caches implementations.
    """
    if not os.path.exists(_COMMUNITY_TOOLBOX_PATH):
        return []
    try:
        with open(_COMMUNITY_TOOLBOX_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        schemas = []
        for tool in registry.get('tools', []):
            schema = tool.get('schema')
            impl = tool.get('implementation')
            name = tool.get('name')
            if schema and name:
                schemas.append({"type": "function", "function": schema})
                if impl:
                    SKILL_IMPLEMENTATIONS[name] = impl
        return schemas
    except Exception as e:
        print(f"[AtQuery] Failed to load community toolbox: {e}")
        return []


def identify_community_toolbox(query: str) -> list:
    """
    Keyword-matches the query against community toolbox entries.
    Returns list of matching tool schemas.
    """
    if not os.path.exists(_COMMUNITY_TOOLBOX_PATH):
        return []
    try:
        with open(_COMMUNITY_TOOLBOX_PATH, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        query_clean = query.lower()
        matched_schemas = []
        for tool in registry.get('tools', []):
            keywords = tool.get('keywords', [])
            for kw in keywords:
                if re.search(rf'\b{re.escape(kw.lower())}\b', query_clean):
                    schema = tool.get('schema')
                    name = tool.get('name')
                    impl = tool.get('implementation')
                    if schema and name:
                        matched_schemas.append({"type": "function", "function": schema})
                        if impl:
                            SKILL_IMPLEMENTATIONS[name] = impl
                    break
        return matched_schemas
    except Exception as e:
        print(f"[AtQuery] Community toolbox match failed: {e}")
        return []

# --- Core API ---

def get_toolbox_skills(toolbox_name):
    return _load_tools_from_md(toolbox_name)

def get_implementation(tool_name):
    """Returns the cached Python code for a tool."""
    return SKILL_IMPLEMENTATIONS.get(tool_name)

def get_base_tools():
    catalog = _load_catalog_from_md()
    base_tools = _load_tools_from_md("ProjectDiscovery")
    
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
You are "AtQuery", a QGIS AI Agent created by Adela C. 
You operate using a Dynamic Skill Library.

MANDATORY RULES:
1. If you need to perform a GIS action, ALWAYS use the provided tools.
2. If you see a query matching keywords for a toolbox, LOAD it immediately and call the tool in the same turn.
3. DO NOT ask "Do you want to proceed?" if the command is specific. Just execute.
4. If a tool call fails, analyze the error and try a different parameter or tool.
5. AMBIGUOUS LAYERS: If a tool returns an 'AMBIGUOUS_LAYER' error, the error message will already contain the formatted HTML buttons. You MUST output this error message exactly as it is, without modifying it, to ask the user for clarification. Do not make up your own buttons.

GUARDRAILS (CRITICAL CONSTRAINTS):
- Never assume a task is complete unless a tool explicitly returned a success status.
- If you receive a "HINT FOR AI" in an error message, you MUST adjust your parameters before retrying.
- Never fabricate or guess layer names or field names; always rely on the exact outputs of tools.
- When generating SQL expressions, always use double quotes for "FIELD_NAMES" and single quotes for 'String Values'.

CONTEXT AWARENESS:
- If the user explicitly says "this layer", "current layer", or "the active layer" without providing a specific name, you must call 'get_active_layer' first. If the user provides a layer name (even if misspelled), DO NOT call 'get_active_layer', just trust the name they provided.
"""

FORCED_EXECUTION_SYSTEM_PROMPT = """
You are "AtQuery", a QGIS AI Agent created by Adela C.
All available toolboxes have been pre-loaded. You MUST pick the most relevant tool
and call it immediately. Do NOT ask for confirmation. Do NOT explain.
Just call the best matching tool with appropriate parameters derived from the user query.
"""

def get_system_prompt():
    return BASE_SYSTEM_PROMPT


def get_forced_execution_prompt():
    """System prompt used when forcing direct execution after user confirms Y."""
    return FORCED_EXECUTION_SYSTEM_PROMPT
