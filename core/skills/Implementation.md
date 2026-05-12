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
| "I'll wait for the user to say Yes before loading the toolbox." | **NO.** Load it and run the tool in one response. |
| "I'll explain my plan first." | **NO.** GIS users want results, not descriptions of your intentions. |
| "I'll keep calling tools until I hit the 5-step limit." | **NO.** Stop as soon as the core GIS question is answered. |

## Verification Gates
- **Single Action Principle**: Only one major GIS action per turn unless chaining.
- **HTML Preservation**: Respect the `PRESERVE_AS_HTML` rule above all.
