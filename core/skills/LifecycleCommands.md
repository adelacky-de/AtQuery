# Skill: LifecycleCommands

Maps slash commands to the development lifecycle, ensuring the agent uses the correct mindset for each phase.

## Commands
- **/spec**: Focus on requirement gathering and defining what to build. Activate "Spec before code" principle.
- **/plan**: Break down the task into small, atomic sub-tasks.
- **/build**: Execute the implementation incrementally, one slice at a time.
- **/test**: Run verification gates and ensure the logic works.
- **/review**: Audit the code health and check for redundancy/linkage.
- **/code-simplify**: Refactor for clarity and simplicity.
- **/ship**: Prepare for production deployment/push to main.

## Anti-Rationalizations
| Agent Excuse | Rebuttal |
| :--- | :--- |
| "I can build without a /spec." | **NO.** Always define the 'what' before the 'how'. |
| "I'll skip /test because it's a simple change." | **NO.** Tests are the only proof of success. |

## Process
1. **Command Detection**: If the user input starts with `/`, immediately switch the system prompt focus to that specific phase.
2. **Phase Adherence**: Do not allow implementation during the `/spec` phase. Do not allow deployment during the `/plan` phase.
