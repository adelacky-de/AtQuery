# AtQuery Harness Rules

These rules are MANDATORY for all development and maintenance of the AtQuery plugin.

## 1. Post-Update Verification
After every code modification, you MUST:
- **Audit Imports**: Ensure all used classes (e.g., `QgsProject`, `QgsFeatureRequest`) are explicitly imported in the file.
- **Linkage Check**: Verify that changes in `core` (e.g., tool schemas) are compatible with the `ui` (e.g., dockwidget loop) and vice-versa.
- **Path Integrity**: Ensure relative imports and file paths remain valid.

## 2. Functional Self-Check
Before declaring a task "complete", you MUST:
- **Dry-Run Analysis**: Trace the logic of the change mentally or via scratch scripts to ensure no edge cases (like empty layers or missing fields) cause crashes.
- **Schema Validation**: Ensure any new tool schemas are valid JSON and match the parameters used in the Python implementation.

## 3. Surgical Edits (Principle of Least Disruption)
- **Focus**: Only modify the specific lines or components identified as problematic.
- **Preservation**: Do not refactor or change functional components that are unrelated to the current task. 
- **Consistency**: Maintain existing naming conventions and UI aesthetics.
