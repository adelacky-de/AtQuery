# Skill: Implementation (Antigravity Assistant)

Guides me through the incremental building of the code, following the "One Slice at a Time" principle.

## Process
1. **Surgical Edits**: Target only the specific lines or functions that need changing.
2. **Context Awareness**: Respect existing variable names and coding styles in the file.
3. **Functional Integrity**: Ensure the code is syntactically correct and type-safe.
4. **Self-Correction**: If an edit fails, re-examine the file and adjust the target range.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll refactor this unrelated function while I'm here." | **NO.** Follow the "Principle of Least Disruption." |
| "The user's code looks messy, I'll rewrite it all." | **NO.** Maintain the user's style unless asked to simplify. |

## Verification Gates
- **Compilation Check**: Run `py_compile` if possible.
- **Linkage Check**: Verify that newly added tools or functions are correctly linked in the main loops.
