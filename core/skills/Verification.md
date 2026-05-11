# Skill: AtQuery-Verification

Guides the local LLM through proving that the GIS result is visible and correct in QGIS.

## Process
1. **Map Feedback**: Confirm if the map canvas was zoomed or refreshed.
2. **Layer Presence**: Verify the new layer exists in the `QgsProject`.
3. **Selection Check**: Confirm the count of selected features.
4. **HTML Integrity**: Ensure no conversational summaries are "hallucinated" over raw HTML tables.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I can't see the map, so I'll assume it worked." | **NO.** Check the "status: success" and zoom count returned by the tool. |
| "I'll summarize the table myself." | **NO.** The HTML Interceptor already showed the raw data. Just say "Here is the data:". |

## Verification Gates
- **Zero Hallucination**: Every "fact" about the map must come from a tool output.
