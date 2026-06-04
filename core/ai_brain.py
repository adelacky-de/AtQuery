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
    Score-based toolbox routing.
    Each toolbox gets a score = number of its keywords found in the query.
    Only the highest-scoring toolbox(es) are loaded, capped at 2.
    This prevents multi-keyword queries from loading too many toolboxes and
    confusing the AI with an overloaded tool list.
    """
    query_clean = query.lower()

    # ── HARD RULE: suppress ProjectDiscovery if a specific layer is named ──
    all_layers = [l.name().lower() for l in QgsProject.instance().mapLayers().values()]
    has_specific_layer = any(l in query_clean for l in all_layers if len(l) > 2)

    # ── INTENT OVERRIDE: resolve the DataInspection vs SelectionTools collision ──
    # "show me / display / what are / list / give me" → display intent → DataInspection wins
    DISPLAY_TRIGGERS = ("show me", "display", "what are", "give me", "list the",
                        "columns", "example values", "what fields", "how many")
    # "select / pick / highlight / choose" → selection intent → SelectionTools wins
    SELECT_TRIGGERS  = ("select ", "pick ", "highlight ", "choose ", "deselect", "clear selection")

    display_intent = any(t in query_clean for t in DISPLAY_TRIGGERS)
    select_intent  = any(t in query_clean for t in SELECT_TRIGGERS)

    catalog = _load_catalog_from_md()
    scores = {}

    for tb in catalog:
        if tb == "ProjectDiscovery" and has_specific_layer:
            continue

        keywords = catalog[tb].get('keywords', [])
        score = sum(1 for kw in keywords if kw.lower() in query_clean)
        if score > 0:
            scores[tb] = score

    if not scores:
        return []

    # ── Apply intent overrides to break ties ──
    if display_intent and not select_intent:
        # Boost DataInspection, dampen SelectionTools
        if "DataInspection" in scores:
            scores["DataInspection"] += 2
        if "SelectionTools" in scores:
            scores["SelectionTools"] = max(0, scores["SelectionTools"] - 1)
    elif select_intent and not display_intent:
        # Boost SelectionTools, dampen DataInspection
        if "SelectionTools" in scores:
            scores["SelectionTools"] += 2
        if "DataInspection" in scores:
            scores["DataInspection"] = max(0, scores["DataInspection"] - 1)

    # Remove zero-score entries that may have been dampened
    scores = {tb: s for tb, s in scores.items() if s > 0}
    if not scores:
        return []

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_score = ranked[0][1]

    # Load only toolboxes within 1 point of the top score, capped at 2
    # (A gap of ≥2 means one toolbox clearly dominates — load only that one)
    result = [tb for tb, s in ranked if s >= top_score - 1][:2]
    return result



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
This core protocol ensures the agent remains disciplined and follows a strict GIS engineering workflow.

## Process
1. **Direct Action**: Every request is an instruction to ACT. Call the relevant tool immediately.
2. **Zero Permission**: Do NOT ask "Would you like me to...". Just do it.
3. **Loop Prevention**: If you have already called a tool in this turn, **STOP**.
4. **Verify**: Always confirm success through feature counts or map zooming.

## Anti-Rationalizations
- **No Chatter**: Do not explain your plan before executing it. Execute first.
- **No Redundant Calls**: If a tool returns "success" or "PRESERVE_AS_HTML", the turn is over.
- **No Passive Waiting**: If a toolbox needs to be loaded, call `load_toolbox_skills` AND the target tool in the same turn.

## FORBIDDEN OUTPUT PHRASES (NEVER write any of these)
Your response MUST NOT contain any of the following phrases or any paraphrase of them:
- "Would you like..."
- "Do you want..."
- "Shall I..."
- "Should I..."
- "Would you like me to proceed..."
- "Is there anything else..."
- "Please let me know if..."
- "Let me know if you need..."
- "To see the actual data values, please use..."
- "I can display the first few rows for verification."
- "Would you like to see more?"
If your response contains any of the above, DISCARD it and respond with ONLY the facts from the tool output.
"""

def get_meta_skills():
    """Reads all markdown files in the skills directory to build the AI's harness."""
    meta_skills = BASE_HARNESS
    skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
    if os.path.exists(skills_dir):
        for f in sorted(os.listdir(skills_dir)):
            if f.endswith('.md'):
                with open(os.path.join(skills_dir, f), 'r', encoding='utf-8') as file:
                    meta_skills += f"\n---\n{file.read()}\n"
    return meta_skills

def get_system_prompt():
    meta = get_meta_skills()
    return f"""You are "AtQuery", a QGIS AI Agent. You answer GIS questions by calling tools. Read each tool's description carefully — it tells you exactly when to use it.

## CORE SKILLS
{meta}

## RULES
1. ALWAYS call a tool. Never respond with text only when tools are available.
2. NEVER invent field names, layer names, or data values. Only report what tools return.
3. After a tool returns data: report only the facts. Do not add questions or suggestions.
4. If a tool returns a feature count: report "Selected X features." and stop.
5. For "show me / display / what are / columns / values / example data" → call get_layer_features_sample.
6. For "select features where X" (simple filter) → call QgsVectorLayer_selectByExpression.
7. For "select top N by field" → call select_features_advanced. Never call it together with selectByExpression.
8. If user says "this layer" or "current layer" → call get_active_layer first. If user names a layer → use that name directly.
9. If user says "buffer/clip/process the selected [X]" and X is NOT a known layer name → call get_layers_with_selection to find which layer has the selection, then operate on that layer.
10. If the query is extremely vague ("do something", "what should I do") with no specific layer or GIS action → respond: "Please provide more specific instructions. What layer or operation did you have in mind?" and do NOT call any tool.
11. If the user asks a conceptual/advice question ("what is a good buffer distance", "how far should", "what is the best approach") → respond: "This is a planning question. For the GIS operation itself, tell me what layer and distance to use." Do NOT call any tool.

CONTEXT AWARENESS:
- If the user says "this layer", "current layer" without a name → call get_active_layer first.
- If the user names a layer (even misspelled) → do NOT call get_active_layer.
"""


def get_forced_execution_prompt():
    """System prompt used when forcing direct execution after user confirms Y."""
    return """You are "AtQuery", a QGIS AI Agent created by Adela C.
All available toolboxes have been pre-loaded. You MUST pick the most relevant tool
and call it immediately. Do NOT ask for confirmation. Do NOT explain.
Just call the best matching tool with appropriate parameters derived from the user query.
"""
