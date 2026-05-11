# Skill: Planning (Antigravity Assistant)

Guides me through the process of analyzing your requests and breaking them into atomic, verifiable coding tasks.

## Process
1. **Analyze Requirements**: Understand the technical constraints (QGIS, Python, PyQt5).
2. **Architecture Check**: Verify imports, linkage, and existing patterns in the workspace.
3. **Task Breakdown**: Create a list of small, focused edits.
4. **Impact Assessment**: Ensure changes don't break unrelated features.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll just edit the whole file at once." | **NO.** Use surgical edits. Smaller chunks are easier to verify. |
| "I don't need to check the imports." | **NO.** Missing imports are the #1 cause of plugin crashes in QGIS. |

## Verification Gates
- **Sequential Logic**: Does each task lead logically to the next?
- **User Alignment**: Confirm the plan with the user before major changes.
