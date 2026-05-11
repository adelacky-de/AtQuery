# Skill: LifecycleCommands

Maps user slash commands to specific development phases and enforces the associated engineering principles.

## Commands
- **/spec**: (Spec before code) Define the exact requirements and edge cases before writing any implementation.
- **/plan**: (Small, atomic tasks) Break the spec down into a list of specific, verifiable sub-tasks.
- **/build**: (One slice at a time) Implement one atomic task from the plan and verify its individual functionality.
- **/test**: (Tests are proof) Run validation scripts or QGIS processing dry-runs to prove the build works.
- **/review**: (Improve code health) Perform a self-audit of imports, linkage, and naming conventions.
- **/code-simplify**: (Clarity over cleverness) Refactor the implementation to be more readable and maintainable.
- **/ship**: (Faster is safer) Finalize the change, update metadata, and commit/push to the repository.

## Process
1. **Command Detection**: If a message starts with a slash command, transition to that specific phase immediately.
2. **Phase Enforcement**: Do not skip from /spec to /build without a /plan.
3. **Verification**: Each phase must end with a clear statement of the outcome (e.g., "Plan generated: [tasks]").

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I'll just build it directly, it's simple." | **NO.** Follow the lifecycle. /spec and /plan are mandatory for all changes. |
| "I don't need to test if I'm sure it works." | **NO.** /test is the only acceptable proof of success. |

## Verification Gates
- **Sequential Integrity**: Ensure the development lifecycle is followed in order.
