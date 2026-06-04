# Skill: AtQuery-Planning

Guides the local LLM through analyzing GIS requests and mapping them to QGIS toolboxes.

## Process
1. **Layer Resolution**: Identify which layers are needed.
2. **Metadata Priority**: If the user asks "Tell me about", "Metadata", or "Columns", prioritize the **DataInspection** toolbox and the `get_layer_metadata` tool.
3. **Toolbox Mapping**: Match keywords to the correct toolbox.
4. **Direct Execution**: Once a tool is identified, **CALL IT IMMEDIATELY**. Do not ask for permission. Execute the call in the same turn.
5. **Tool Chaining**: If a toolbox needs loading, call `load_toolbox_skills` AND the target tool in the same response.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll ask the user if they want me to load the tool." | **NO.** You are an autonomous agent. Load the tools you need and execute the request. |
| "I'll explain my plan first." | **NO.** Actions speak louder than words. Execute the tool first, then explain the result. |

## Verification Gates
- **Capability Check**: Do I have a toolbox loaded that can handle this request?
