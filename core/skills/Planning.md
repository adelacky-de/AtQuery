# Skill: Planning-And-Task-Breakdown

Guides the agent through breaking down complex GIS requests into smaller, manageable sub-tasks.

## Process
1. **Analyze Requirements**: Understand the spatial and attribute constraints.
2. **Step Mapping**: Map the request to specific toolbox skills (e.g., Buffer -> Select -> Style).
3. **Sequence Optimization**: Determine the most efficient order of operations.
4. **Tool Selection**: Identify the exact tools needed for each step.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll just do it all in one giant tool call." | **NO.** Complex tasks should be executed step-by-step for better error recovery. |
| "I'll skip planning for simple requests." | **NO.** Even simple requests benefit from a clear mental model of the expected output. |

## Verification Gates
- **Plan Clarity**: The agent must be able to state the steps it is about to take if asked.
- **Dependency Check**: Ensure that step N+1 has the inputs it needs from step N.
