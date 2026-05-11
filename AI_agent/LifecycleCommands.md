# Skill: LifecycleCommands

Maps user slash commands to specific development phases and enforces the associated engineering principles.

## Commands
- **/spec**: Define the exact requirements and edge cases.
- **/plan**: Break the spec down into atomic sub-tasks.
- **/build**: Implement one atomic task and verify.
- **/test**: Run validation scripts or QGIS dry-runs.
- **/review**: Perform a self-audit of imports and linkage.
- **/code-simplify**: Refactor for clarity.
- **/ship**: Finalize the change and push.

## Process
1. **Command Detection**: If a message starts with a slash command, transition to that specific phase immediately.
2. **Phase Enforcement**: Do not skip steps.
3. **Verification**: Each phase must end with a clear statement of the outcome.
