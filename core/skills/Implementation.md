# Skill: Incremental-Implementation

Guides the agent through the step-by-step execution of a GIS workflow, ensuring each tool call is valid.

## Process
1. **Tool Invocation**: Generate the tool call with precise parameters.
2. **Error Monitoring**: Check the tool output for "HINT FOR AI" or "AMBIGUOUS_LAYER".
3. **Self-Correction**: If an error occurs, analyze the hint and retry with adjusted parameters immediately.
4. **State Management**: Track which layers were created or modified in previous steps.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "The tool failed, I'll ask the user what to do." | **NO.** Use the "HINT FOR AI" to try and fix it yourself first. |
| "I'll use default values without checking the CRS." | **NO.** Implementation must be context-aware (units, projection, etc.). |

## Verification Gates
- **Success Confirmation**: Every implementation step must conclude with a "status: success" before the next step starts.
