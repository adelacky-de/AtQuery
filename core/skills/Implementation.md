# Skill: Incremental-Implementation

Guides the agent through the step-by-step execution of a GIS workflow, ensuring each tool call is valid and loops are prevented.

## Process
1. **Tool Invocation**: Generate the tool call with precise parameters.
2. **Error Monitoring**: Check the tool output for "HINT FOR AI" or "AMBIGUOUS_LAYER".
3. **Loop Detection**: If you have already called a tool with the same or similar parameters in this turn, **STOP IMMEDIATELY**.
4. **State Recognition**: If a tool returns a success status or "PRESERVE_AS_HTML", assume the user has seen the result. Do not repeat the call.
5. **Termination**: Once a tool has provided a valid result, transition to the /test or /review phase. Do not invent "next steps" unless explicitly asked.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "The user might want more rows, I'll call it again." | **NO.** Return the first set. Let the user ask for more if needed. |
| "The tool returned success, but I'll call a different one just to be sure." | **NO.** One successful action per query is the standard unless a complex multi-step plan was agreed upon. |
| "I'll keep calling tools until I hit the 5-step limit." | **STRICT NO.** Efficiency is key. Stop as soon as the core question is answered. |

## Verification Gates
- **Redundancy Check**: Ensure no tool name appears more than twice in a single conversation turn.
- **Success Acknowledgment**: If a tool returned "status: success", your next message MUST be a conclusion or a confirmation.
