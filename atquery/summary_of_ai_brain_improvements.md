# Summary of AI Brain Improvements and Recommendations

## 1. Initial State
- The AI was struggling to correctly interpret user requests and translate them into QGIS tool calls.
- Issues included misinterpreting tool schemas, generating conversational text, and not adhering to the specified workflow.

## 2. Changes Implemented

### 2.1. Tool Schema and Documentation (`core/ai_brain.py` and `core/pyqgis_tools.md`)
- **Action:** Added new QGIS tools (`QgsVectorLayer_setSingleSymbolRenderer`, `QgsVectorLayer_crs`, `processing_run_reprojectlayer`) to `TOOLS_SCHEMA` in `core/ai_brain.py`.
- **Action:** Documented these new tools, along with existing ones, in `core/pyqgis_tools.md` with logic and code examples.
- **Action:** Initially, `pyqgis_tools.md` was included directly in the `get_system_prompt` to provide the AI with a knowledge base.
- **Action:** Later, the inclusion of `pyqgis_tools.md` in the system prompt was removed to simplify the prompt and reduce conversational output.

### 2.2. System Prompt Refinement (`BASE_SYSTEM_PROMPT` in `core/ai_brain.py`)
- **Action:** Iteratively refined `BASE_SYSTEM_PROMPT` to be more explicit, direct, and rule-based.
- **Key additions/modifications:**
    - Stricter workflow definition ("ALWAYS START HERE", "INSPECT THE DATA", "EXECUTE THE ACTION").
    - Explicit rules: "NO CONVERSATION", "JSON ONLY", "LAYER NAMES ARE EXACT", "SQL QUOTING IS CRITICAL", "ONE GOAL, ONE TOOL", "DO NOT HALLUCINATE", "STRICT TYPE ADHERENCE".
    - Detailed examples for various tool calls, including correct JSON formatting and argument types.
    - Specific instructions on boolean (`true`/`false`) and number types, and forbidding `<|python_tag|>`.

### 2.3. Test Suite Expansion and Robustness (`test_brain_local.py`)
- **Action:** Expanded `TEST_SUITE` with new test questions covering buffer creation, topological relationships, CRS changes, and layer styling.
- **Action:** Updated `mock_handle_tool_call` to support the new tools and provide mock responses.
- **Action:** Implemented and iteratively enhanced `repair_json_response` function to:
    - Aggressively extract JSON objects from potentially malformed AI output using regex.
    - Attempt to fix common JSON issues (e.g., `parameters` to `arguments`).
    - Perform schema-based type conversion for tool arguments (e.g., string "true" to boolean `True`, string "10" to number `10`).
    - Strip conversational text, ensuring only JSON tool calls are processed.
    - Added checks for `tool_args` to be a dictionary.

## 3. Failed/Caught Cases and Persistent Issues

Despite the extensive changes, several issues persisted, indicating fundamental challenges with the model's behavior:

-   **Conversational Text and `<|python_tag|>`:** The AI frequently included conversational text and the `<|python_tag|>` in its output, even with explicit instructions and a repair mechanism designed to strip it. This suggests a strong tendency of the model to generate natural language.
-   **Malformed JSON Output:** While `repair_json_response` significantly improved parsing, the AI often produced JSON that was initially malformed (e.g., missing braces, incorrect nesting), requiring aggressive regex and repair logic. This indicates the model struggles with consistent adherence to strict JSON syntax.
-   **Incorrect Argument Types:** Even with `_convert_arg_type` and explicit prompt instructions, the AI often provided string representations for boolean and number parameters (e.g., `refresh: "false"`, `distance: "10"`), rather than native JSON booleans/numbers.
-   **Chaining Multiple Tool Calls:** The "ONE GOAL, ONE TOOL" rule was frequently violated, with the AI attempting to chain multiple tool calls in a single response.
-   **Misinterpretation of Tool Usage and Logic:**
    -   Attempting to pass SQL expressions to tools that don't accept them (e.g., `processing_run_native_buffer` with `sql`).
    -   Using incorrect predicates or non-existent layer names in spatial queries.
    -   Not following the "DISCOVER -> INSPECT -> ACTION" workflow consistently.

## 4. Final Recommendation for Improvement

The persistent issues suggest that the current model (llama3.2:3b-instruct-q4_K_M) has inherent limitations in strictly adhering to structured output formats and complex rule sets, especially when combined with natural language understanding.

**Primary Recommendation: Model Selection**
-   **Explore alternative models:** The most impactful improvement would likely come from using a model specifically fine-tuned or inherently better at producing structured, JSON-only output and strictly following instructions. Models designed for function calling or code generation might perform better.

**Secondary Recommendations (if model change is not feasible):**

-   **Further Refine `TOOLS_SCHEMA`:** Ensure descriptions are as unambiguous as possible, explicitly stating expected input/output formats where the model struggles.
-   **Advanced Output Parsing/Validation:** While `repair_json_response` is robust, consider external libraries or more sophisticated parsing techniques if the model continues to produce highly malformed JSON. This would be a mitigation, not a solution to the root cause.
-   **Iterative Feedback Loop:** Implement a system where the AI receives explicit feedback on its incorrect tool calls (e.g., "Error: `distance` expects a number, received a string"). This could be part of the prompt in subsequent turns.
-   **Simplify Complex Tasks:** Break down complex user requests into smaller, more manageable sub-tasks for the AI, reducing the cognitive load and potential for errors.
