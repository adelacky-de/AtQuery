# Skill: AtQuery-Implementation

Guides the local LLM through executing QGIS tool calls without redundant loops or passive chatter.

## Process
1. **Direct Tool Invocation**: Your response MUST contain at least one tool call if a relevant tool exists.
2. **Zero Permission**: Do not ask "Should I proceed?". Proceed by default. Every user query is an implicit instruction to ACT.
3. **Loop Termination**: If a tool returned "success" or "PRESERVE_AS_HTML", **STOP**. Do not call the same tool again in this turn.
4. **Result Recognition**: If the UI interceptor returns a message about HTML being displayed, assume the user has the data.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll provide a conversational example to be helpful." | **CRITICAL NO.** Never provide text-based examples of GIS data (e.g. "ID: 12345 | Name: Alice"). ONLY show the raw tool output. If a tool succeeds, say "Here is the data:" and stop. |
| "I'll wait for the user to say Yes before loading the toolbox." | **NO.** Load it and run the tool in one turn. |
| "I'll explain my logic first." | **NO.** Execute first, talk later. |
| "I'll make up field names if I'm not sure." | **NO.** Call `QgsVectorLayer_fields` first. |

## Verification Gates
- **Single Action Principle**: Only one major GIS action per turn unless chaining.
- **HTML Preservation**: Respect the `PRESERVE_AS_HTML` rule above all.
- **Zero Hallucination**: No made-up records or example tables in the final response.
- **Direct Action**: At least one tool call per user request turn.
