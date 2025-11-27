# AtQuery Documentation
AI-Powered QGIS Assistant Plugin

## Table of Contents
- [1. What is AtQuery?](#1-what-is-atquery)
- [2. System Requirements](#2-system-requirements)
- [3. Installation](#3-installation)
- [4. Getting Started](#4-getting-started)
- [5. How to Use AtQuery](#5-how-to-use-atquery)
- [6. Query Examples](#6-query-examples)
- [7. Available Operations](#7-available-operations)
- [8. Tips and Best Practices](#8-tips-and-best-practices)
- [9. Troubleshooting](#9-troubleshooting)
- [10. Technical Details](#10-technical-details)
## 1. What is AtQuery?

AtQuery is a QGIS plugin that brings AI-powered natural language processing to
your GIS workflows. Instead of manually navigating menus and dialogs, you can
simply type what you want to do in plain English, and AtQuery will execute the
appropriate QGIS operations.

**Key Features:**
- Natural language interface for QGIS operations
- Layer selection and filtering
- Spatial queries (intersections, buffers, distance queries)
- Attribute operations (joins, field queries)
- Buffer and bounding box creation
- Powered by local AI (Ollama) - your data stays private

## 2. System Requirements

**Required Software:**
- QGIS 3.x or later
- Ollama (local LLM server)
- Model: llama3.2:3b-instruct-q4_K_M
- Python packages: requests, json (usually pre-installed with QGIS)

**Operating Systems:**
- macOS
- Windows
- Linux

**Hardware Recommendations:**
- Minimum 8GB RAM (16GB recommended for better performance)
- ~4GB disk space for Ollama and the model

## 3. Installation

### Step 1: Install Ollama
1. Download Ollama from [https://ollama.com](https://ollama.com)
2. Install Ollama following the instructions for your operating system
3. Start Ollama (it runs as a background service)

### Step 2: Install the AI Model
Open your terminal/command prompt and run:

```bash
ollama pull llama3.2:3b-instruct-q4_K_M
```

This will download the required AI model (~2GB download).

### Step 3: Install AtQuery Plugin
**Option A - QGIS Plugin Manager (if published):**
1. Open QGIS
2. Go to Plugins → Manage and Install Plugins
3. Search for "AtQuery"
4. Click Install

**Option B - Manual Installation:**
1. Copy the AtQuery folder to your QGIS plugins directory:
   - Windows: `C:\Users\YourName\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

2. Restart QGIS
3. Enable the plugin: Plugins → Manage and Install Plugins → Installed → Check AtQuery

### Step 4: Verify Installation
1. After installing, click the AtQuery icon in the toolbar
2. The AtQuery panel should appear on the right side
3. You should see: "🟢 Ollama API Connected. Checking for model..."
4. If successful: "🟢 Model 'llama3.2:3b-instruct-q4_K_M' found. Ready."

## 4. Getting Started

**Opening AtQuery:**
- Click the AtQuery icon in the QGIS toolbar, OR
- Go to menu: Plugins → AtQuery → AI Chat for QGIS

**The AtQuery Panel:**
- Chat display area (shows conversation history)
- Input field (where you type your requests)
- Send button

**First Steps:**
1. Load some layers into your QGIS project
2. Open AtQuery from the toolbar
3. Try a simple query: "What are the names of all the layers?"
4. The AI will respond with the list of layers in your project

## 5. How to Use AtQuery

**Basic Usage Pattern:**
1. Type your request in plain English
2. Press Enter or click Send
3. The AI processes your request and executes the appropriate QGIS operation
4. Results are shown in the chat and applied to your QGIS project

**Query Structure Tips:**
- Be specific about layer names when possible
- If unsure of exact names, use partial names (AI will suggest corrections)
- Mention what you want to SELECT, CREATE, COUNT, or QUERY
- For spatial operations, mention the relationship (within, intersect, etc.)

**What Happens Behind the Scenes:**
1. AI parses your natural language request
2. Identifies the operation type and required parameters
3. If information is missing, AI asks for it or retrieves it using tools
4. Executes the appropriate QGIS function
5. Reports the result back to you

**Confirmation Prompts:**
If the AI is unsure about a layer or field name, it will ask:
`"Did you mean 'LayerName'? {y/N}"`

Respond with 'y' or 'yes' to confirm, or 'n'/'no' to decline.

## 6. Query Examples

### **Layer Information Queries:**
- "What are the names of all the layers?"
- "What fields does the Roads layer have?"
- "How many features are in the Roads layer?"
- "Count the number of features in Buildings"

### **Selection Queries:**
- "Select the Southern District in the AdminArea layer"
- "Select features where population > 100000"
- "Find all roads with type = 'highway'"
- "Select buildings that contain 'School' in their name"

### **Multiple Conditions:**
- "Select Southern District or Eastern District in AdminArea"
- "Find areas where population > 50000 AND area < 1000000"
- "Select features where name is 'District A' or 'District B'"

### **Spatial Queries:**
- "Select houses within 500m of schools"
- "Select parcels that are inside urban zones"
- "Select roads that intersect with rivers"
- "Find buildings that touch property boundaries"
- "Find buildings that touch property boundaries"
- "Select features in layer A that are within layer B"

### **Buffer Operations:**
- "Create a 500m buffer for all features in WindEnergy layer"
- "Create a 10km buffer for Schools"
- "Buffer the Buildings layer by 100m"

### **Bounding Box Creation:**
- "Help me create a bounding box"
- "Create a bounding box layer from the current map extent"

### **Attribute Operations:**
- "Join the ParcelInfo layer to the Parcels layer using PARCEL_ID field"

### **Field Queries vs Counting:**
- "How many features in Buildings?" → Returns a NUMBER
- "What fields does Buildings have?" → Returns FIELD NAMES
- "Which fields are in the Roads layer?" → Returns FIELD NAMES

## 7. Available Operations

### Information Retrieval:
- `get_layer_list`: Lists all layers in the project
- `get_layer_details`: Shows fields and metadata for a specific layer

### Feature Selection:
- `select_features`: Selects features based on attribute or spatial criteria
  - Supports SQL-like expressions
  - Supports spatial predicates (`overlay_intersects`, `overlay_within`, etc.)
  - Automatically zooms to selected features

### Layer Creation:
- `create_buffer`: Creates buffer zones around features
  - Parameters: layer name, distance (in map units/meters)
  - Creates smooth polygonal buffers
  
- `create_bbox_layer`: Creates rectangular bounding box
  - Can use current map extent or custom coordinates

### Attribute Operations:
- `join_attributes`: Joins attributes from one layer to another
  - Based on matching field values
  - Can add custom prefix to joined fields

### Spatial Predicates:
- `overlay_intersects`: Features that intersect with another layer
- `overlay_within`: Features contained within another layer
- `overlay_nearest`: Features within a certain distance of another layer
- `overlay_touches`: Features that touch (share boundary with) another layer

## 8. Tips and Best Practices

### For Best Results:
1. **Be Specific:** Use exact layer names when you know them
   ✓ "Select features in AdminArea_DCD_20230609"
   ✗ "Select stuff from that admin layer"

2. **Start Simple:** If unsure, ask for information first
   ✓ "What layers are in my project?"
   ✓ "What fields does LayerX have?"
   Then build your query based on the response

3. **Use Clear Relationships:** For spatial queries, be explicit
   ✓ "Select parcels that are inside UrbanZones"
   ✓ "Select roads that intersect with Rivers"

4. **Buffer Distances:** Specify units clearly
   ✓ "Create a 500m buffer" (meters)
   ✓ "Create a 10km buffer" (will be converted to 10000m)

5. **Count vs Fields:** Use clear language
   ✓ "How many features..." → returns a count
   ✓ "What fields..." → returns field names

### Common Patterns:
- **Exploration:** Start with "What layers..." or "What fields..."
- **Selection:** Use "Select", "Find", "Filter" keywords
- **Creation:** Use "Create a buffer", "Make a bounding box"
- **Spatial:** Use "within", "intersect", "touch", "near"
- **Counting:** Use "How many", "Count the"

### Handling Errors:
If the AI doesn't understand:
1. Rephrase your query more simply
2. Break complex requests into steps
3. Check layer names are spelled correctly
4. Verify the layer is loaded in your QGIS project

### If Selections Don't Work:
1. Check field names with "What fields does LayerName have?"
2. Verify field values match exactly (case-sensitive)
3. Use double quotes for field names: `"FIELD_NAME"`
4. Use single quotes for string values: `'Value'`

## 9. Troubleshooting

**Problem: "Ollama API not found"**
**Solution:**
- Ensure Ollama is installed and running
- Check if `http://localhost:11434` is accessible
- Restart Ollama service
- On macOS: Check if Ollama app is running in menu bar
- On Windows: Check if Ollama service is running in Task Manager

**Problem: "Model not found"**
**Solution:**
- Run in terminal: `ollama pull llama3.2:3b-instruct-q4_K_M`
- Wait for download to complete
- Restart QGIS

**Problem: "Layer not found"**
**Solution:**
- Check exact layer name with "What are the names of all the layers?"
- Layer names are case-sensitive
- Use the exact name shown by the AI

**Problem: "Field not found"**
**Solution:**
- Ask "What fields does LayerName have?"
- Use exact field names (case-sensitive)
- Field names should be in double quotes in SQL expressions

**Problem: AI gives wrong results**
**Solution:**
- Break your request into smaller steps
- First get layer info, then construct your query
- Verify with "What fields..." before complex selections

**Problem: Buffer/join operations fail**
**Solution:**
- Ensure input layer is a vector layer
- Check that layer exists in project
- For joins, verify both layers have the join field
- For buffers, ensure distance is a valid number

**Problem: Slow responses**
**Solution:**
- This is normal for first query (model loading)
- Subsequent queries should be faster
- Complex spatial operations may take longer
- Consider using a more powerful computer for large datasets

## 10. Technical Details

### Architecture:
AtQuery uses a tool-calling architecture where the AI model selects and 
executes specific QGIS operations based on your natural language input.

### Components:
1. AI Brain (`ai_brain.py`):
   - Tool definitions (schema)
   - System prompt (AI behavior rules)
   - Example queries for AI training

2. Dock Widget (`AtQuery_dockwidget.py`):
   - User interface
   - Tool execution handlers
   - QGIS API integration

3. Ollama Integration:
   - Local LLM server (runs on your machine)
   - Model: `llama3.2:3b-instruct-q4_K_M`
   - API endpoint: `http://localhost:11434/api/chat`

### Data Privacy:
- All processing happens locally on your machine
- No data is sent to external servers
- Your GIS data remains completely private
- Ollama runs entirely offline (after model download)

### Supported SQL Syntax:
AtQuery supports QGIS expression syntax including:
- Comparison: `=`, `!=`, `>`, `<`, `>=`, `<=`
- Logical: `AND`, `OR`, `NOT`
- Pattern matching: `LIKE`, `IN`
- Spatial: `overlay_*` functions
- Mathematical: `+`, `-`, `*`, `/`, `%`

### Memory Layers:
Buffer and some processing operations create temporary "memory" layers.
These layers are not saved automatically. To persist them:
1. Right-click the layer in Layers panel
2. Export → Save Features As...
3. Choose format and location

### Buffer Parameters:
The `create_buffer` tool uses these defaults:
- `SEGMENTS`: 5 (smooth curves)
- `END_CAP_STYLE`: Round
- `JOIN_STYLE`: Round
- `DISSOLVE`: False (keeps individual features)

### Performance Considerations:
- First query after starting QGIS is slower (model loading)
- Large layers (>10,000 features) may take longer for spatial queries
- Buffer operations scale with feature count and complexity
- Ollama uses ~2-4GB RAM when active

### Customization:
Advanced users can modify:
- `ai_brain.py`: Add custom tools, modify system prompt, add examples
- Model selection: Change to other Ollama-compatible models
- Tool parameters: Adjust buffer settings, join options, etc.
For more information and updates, visit:
[https://github.com/your-repo/AtQuery](https://github.com/your-repo/AtQuery) (if published)

For QGIS documentation: [https://docs.qgis.org](https://docs.qgis.org)
For Ollama documentation: [https://ollama.com/docs](https://ollama.com/docs)

---
**VERSION:** 1.0
**LAST UPDATED:** 2025-11-27
