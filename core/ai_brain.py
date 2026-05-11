import os
import json
import re
from qgis.core import QgsProject

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

def identify_toolboxes(query: str) -> list:
    """
    Keyword-matches the query against toolbox names.
    Returns list of toolbox names to load.
    """
    query_clean = query.lower()
    
    # ── HARD RULE: PREVENT ACTIVE LAYER DISTRACTION ──
    # If the user provides a specific layer name, we skip ProjectDiscovery (which triggers get_active_layer)
    # to prevent the AI from getting confused by the 'currently active' layer.
    all_layers = [l.name().lower() for l in QgsProject.instance().mapLayers().values()]
    has_specific_layer = any(l in query_clean for l in all_layers if len(l) > 2)
    
    matched = []
    catalog = _load_catalog_from_md()
    for tb in catalog:
        # Skip ProjectDiscovery if we have a specific layer name target
        if tb == "ProjectDiscovery" and has_specific_layer:
            continue
            
        keywords = catalog[tb].get('keywords', [])
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw.lower())}\b', query_clean):
                matched.append(tb)
                break
    return matched


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

# --- Base Harness (Hardcoded to ensure functionality even if skills/ directory is missing) ---
BASE_HARNESS = """
# Skill: CoreHarness
This core protocol prevents infinite tool loops and ensures efficiency.

## Operational Discipline
1. **Single Action**: Perform one major GIS action per turn.
2. **Loop Prevention**: If you have already called a tool in this turn, **STOP**.
3. **Result Recognition**: If a tool returns success or "PRESERVE_AS_HTML", the task is finished. Do not repeat.
4. **Abort**: If a tool fails twice with same parameters, ask for clarification.
"""

def get_meta_skills():
    """Reads all markdown files in the skills directory to build the AI's harness."""
    meta_skills = BASE_HARNESS
    skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
    if os.path.exists(skills_dir):
        for f in sorted(os.listdir(skills_dir)):
            if f.endswith('.md'):
                with open(os.path.join(skills_dir, f), 'r') as file:
                    meta_skills += f"\n---\n{file.read()}\n"
    return meta_skills

def get_system_prompt():
    meta = get_meta_skills()
    return f"""You are "AtQuery", a QGIS AI Agent created by Adela C. 
You operate using a Dynamic Skill Library and follow a strict "Agent Skills" engineering harness.

## CORE HARNESS SKILLS
{meta}

## OPERATIONAL RULES
- Never assume a task is complete unless a tool explicitly returned a success status.
- If you receive a "HINT FOR AI" in an error message, you MUST adjust your parameters before retrying.
- Never fabricate or guess layer names or field names; always rely on the exact outputs of tools.
- CRITICAL: If a tool returns "PRESERVE_AS_HTML", you MUST output the HTML code EXACTLY. DO NOT summarize, DO NOT re-format, DO NOT add a summary, DO NOT convert to markdown, and DO NOT add any conversational text before or after the table. Your response for that tool must be ONLY the HTML table.
- When generating SQL expressions:
    - Map symbols like '&' to 'AND', '|' to 'OR', and ensure strings are in single quotes.
    - Always use double quotes for "FIELD_NAMES" and single quotes for 'String Values'.
    - If a user mentions a value like "Central & Western", check if the actual field value is "Central and Western" by sampling the data first if unsure.

CONTEXT AWARENESS:
- If the user explicitly says "this layer", "current layer", or "the active layer" without providing a specific name, you must call 'get_active_layer' first. 
- If the user provides a layer name (even if misspelled), you MUST NOT call 'get_active_layer'. Just use the name they provided.
"""

def get_forced_execution_prompt():
    """System prompt used when forcing direct execution after user confirms Y."""
    return """You are "AtQuery", a QGIS AI Agent created by Adela C.
All available toolboxes have been pre-loaded. You MUST pick the most relevant tool
and call it immediately. Do NOT ask for confirmation. Do NOT explain.
Just call the best matching tool with appropriate parameters derived from the user query.
"""
