# Skill: AtQuery-Implementation

Guides the local LLM through executing QGIS tool calls without redundant loops.

## Process
1. **Parameter Precision**: Use exact layer and field names derived from the planning phase.
2. **Loop Termination**: If a tool returned "success" or "PRESERVE_AS_HTML", **STOP**. Do not call the same tool again in this turn.
3. **State Awareness**: Track if a new layer was added to the `QgsProject`. Use the new layer name in subsequent steps.
4. **Result Recognition**: If the UI interceptor returns a message about HTML being displayed, assume the user has the data.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll keep calling tools until I hit the 5-step limit." | **NO.** Stop as soon as the core GIS question is answered. |
| "The user asked for 'records', I'll call sample 5 times." | **NO.** One call to `get_layer_features_sample` is enough. Let the user ask for more. |

## Verification Gates
- **Single Action Principle**: Only one major GIS action per turn unless chaining.
- **HTML Preservation**: Respect the `PRESERVE_AS_HTML` rule above all.
