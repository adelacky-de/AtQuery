# Skill: Verification-And-Quality

Guides the agent through verifying that the GIS result matches the user's intent and meets quality standards.

## Process
1. **Visual Confirmation**: Zoom the map to the result (if applicable).
2. **Data Integrity**: If a table was requested, ensure it is rendered as high-fidelity HTML.
3. **Clean-up**: Remove any temporary layers that are no longer needed (if requested).
4. **Final Reporting**: Provide a clear, concise summary of the actions taken.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "It looks right, I'm done." | **NO.** Verify feature counts or specific attribute values if possible. |
| "I'll summarize the table records myself." | **NO.** Let the HTML Interceptor handle the data display to prevent hallucination. |

## Verification Gates
- **Intent Matching**: Does the final map state reflect exactly what the user asked for?
- **No Hallucinations**: Ensure no data was "made up" during the final summary.
