# AtQuery: AI-Powered Natural Language Interface for QGIS

[Implementation Guide (Build from Scratch)](file:///Users/adelachu/Desktop/WWU/AtQuery/atquery/docs/implementation_guide.md)

AtQuery is a QGIS plugin that enables users to query, analyze, and automate geospatial tasks using natural language. It leverages local Large Language Models (LLMs) to eliminate the need for manual PyQGIS scripting or complex SQL expression building.

## 1. Project Objective

The primary goal of AtQuery is to democratize GIS analysis by making QGIS more accessible through a natural language chat interface. 

- **Accessibility**: Users can perform complex operations without knowing PyQGIS or SQL.
- **Privacy & Security**: Powered by a local Ollama instance, ensuring no data leaves the user's machine.
- **Accuracy**: Implements a rigorous verification loop to prevent AI "hallucinations" regarding layer and field names.
- **Workflow Acceleration**: Speeds up repetitive tasks like selection, buffering, and attribute joins.

## 2. File Structure & Components

```text
atquery/
├── __init__.py                # Plugin initialization
├── AtQuery.py                 # Main entry point & menu logic
├── metadata.txt               # QGIS Plugin metadata
├── config/                    # Configuration & build settings
│   ├── .gitignore             # Git exclusion rules
│   ├── pb_tool.cfg            # Build & packaging config
│   ├── pylintrc               # Linting rules
│   └── pyrightconfig.json     # Type checking config
├── core/                      # Core logic & AI engine
│   └── ai_brain.py            # Tool schemas & system instructions
├── ui/                        # User interface components
│   └── AtQuery_dockwidget.py  # Chat interface & logic
├── resources/                 # Assets & compiled resources
│   ├── Icon_AtQuery.jpg       # Plugin icon
│   ├── resources.py           # Resource binary
│   ├── resources_rc.py        # Compiled resource file
│   └── resources.qrc          # Resource definition
├── data/                      # Sample data for tests/demo
│   └── AdminArea_DCD_...csv   # Administrative area data
├── docs/                      # Documentation & help
│   ├── documentation.md       # Project documentation (this file)
│   ├── implementation_guide.md # Step-by-step build guide
│   └── help/                  # HTML help files
├── utils/                     # Helper scripts 
│   ├── installer_utils.py     # Setup & installer logic
│   ├── plugin_upload.py       # Plugin publishing script
│   └── scripts/               # Build & i18n scripts
└── test/                      # Testing suite
    └── ...                    # Unit and integration tests
```

### Component Details
- **Root Files**: Contains the essential files for QGIS to recognize and load the plugin.
- **core/**: The "brains" of the operation, where the AI's tool schemas and behavior are defined.
- **ui/**: All visual elements, including the dockable chat panel and its interaction logic.
- **config/**: Centralized location for development environment and build tools.
- **resources/**: Manages the plugin's icons and compiled assets.
- **utils/**: Support logic for background tasks like installing Ollama or uploading the plugin.
- **docs/**: Comprehensive guides, built-in help, and a step-by-step implementation guide.

## 3. Main Techniques Used

### Local LLM (Ollama)
AtQuery integrates with **Ollama**, an open-source framework for running LLMs locally. This ensures low latency, zero API costs, and full data sovereignty.

### MCP (Model Context Protocol) Loop
The plugin employs a "Mini-MCP" style tool-calling loop. When a user sends a query:
1.  **Intent Extraction**: The AI identifies the desired action (e.g., "Select features").
2.  **Schema Verification**: Instead of guessing, the AI calls tools to `get_layer_list` and `get_layer_details`.
3.  **Corrective Feedback**: If the AI detects a mismatch (e.g., a misspelled field), it prompts the user for correction rather than executing incorrect code.
4.  **Execution**: Once parameters are verified, the AI generates the precise PyQGIS command or SQL expression.

### PyQGIS Integration
The plugin translates high-level intents into native **PyQGIS** calls. This allows the AI to interact directly with the QGIS canvas, layers, and processing algorithms (like `native:buffer`).

## 4. Simulated Walkthrough

Here is a step-by-step example of how AtQuery handles a natural language request.

### Scenario: Selecting specific features from a layer

**Step 1: User Input**  
> *"Select the Southern District in the AdminArea layer."*

**Step 2: Layer Verification (Internal)**  
The AI brain realizes it needs the exact layer name.  
**Action:** Calls `get_tools().get_layer_list()`.  
**Result:** `['AdminArea_DCD_20230609.gdb_converted', 'Parks_Primary']`.  
The AI maps "AdminArea" to the matching full name.

**Step 3: Field Verification (Internal)**  
The AI brain checks which fields contain "Southern District".  
**Action:** Calls `get_layer_details(layer_name='AdminArea_DCD_20230609.gdb_converted')`.  
**Result:** Fields include `['OBJECTID', 'NAME_EN', 'SHAPE_Area']`.

**Step 4: SQL Generation & Execution**  
The AI constructs the final tool call.  
**Action:** Calls `select_features(layer_name='...', sql='"NAME_EN" = \'Southern District\'')`.

**Step 5: Visual Feedback**  
QGIS highlights the Southern District on the map and zooms to the selection.  
**AI Response:** *"Selected 1 feature in AdminArea_DCD_20230609.gdb_converted."*

## 5. Project Origins

This project was initialized using the **QGIS Plugin Builder** tool. The automated testing suite found in the `test/` directory is a standard package generated by the tool to ensure high-quality and reliable QGIS plugin development.

---
© 2026 AdelaC
