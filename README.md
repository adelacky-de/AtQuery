# 🌍 AtQuery: The Agentic QGIS Assistant

**AtQuery** is a QGIS plugin that brings Agentic AI directly to your geospatial workspace. By bridging the gap between natural language and **PyQGIS**, AtQuery allows you to query, analyze, and automate GIS workflows without writing a single line of code.

---

## 🚀 Key Features

- **Natural Language GIS**: No more searching through menus. Ask QGIS questions like *"Buffer the parks by 100m."*
- **Agentic Reasoning**: Powered by a dynamic tool-calling loop. The AI analyses your query, extracts keywords, checks your layers, and chooses the right GIS tool autonomously.
- **Local & Private**: Runs entirely on your machine using **Ollama**. Your data never leaves your computer — zero API costs, total privacy.
- **Modular Skill Library**: Capabilities are organized into "Toolboxes" (Markdown files). Only the skills relevant to your request are loaded into context.
- **Self-Expanding Skills**: If AtQuery lacks a built-in skill, click *"Search & Learn New Skill"* — the AI synthesizes a new PyQGIS tool from its knowledge and saves it to `community_toolbox.json` for future use.
- **Ambiguity Resolution**: When multiple layers match your query, AtQuery shows a clickable list so you can pick the exact layer you want.

---

## ⚙️ How It Works — Logic Workflow

Every query goes through a structured 5-stage pipeline:

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 1 — Keyword Routing                      │
│  Query is matched against toolbox.md            │
│  Each toolbox gets a SCORE = keyword hit count  │
│  Intent detected: DISPLAY vs SELECT             │
│  → Only top-scoring toolbox(es) loaded (max 2) │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 2 — Tool Schemas Loaded                  │
│  Matched .md files parsed for:                  │
│  - JSON tool schemas (sent to AI)               │
│  - Python implementations (cached for exec)     │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 3 — Agentic Loop (max 5 steps)           │
│  POST query + tools → Ollama (qwen2.5:3b)       │
│                                                 │
│  AI responds with a tool_call                   │
│   ├─ load_toolbox_skills → expand tool list     │
│   ├─ Real GIS tool → exec() Python code         │
│   │   ├─ PRESERVE_AS_HTML → render table, STOP  │
│   │   ├─ AMBIGUOUS_LAYER → show click list      │
│   │   └─ Error × 2 → circuit breaker, abort     │
│   └─ No tool_call → display AI text, done       │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 4 — Result Rendering                     │
│  HTML tables rendered directly in chat          │
│  Hallucination guard: if AI invents a data      │
│  table after metadata-only call → stripped      │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 5 — Memory                               │
│  Saves: "Completed using: [tool_name]."         │
│  Only 1 prior turn kept → prevents context      │
│  poisoning across multi-turn conversations      │
└─────────────────────────────────────────────────┘
```

### Keyword Routing — Toolbox Catalog

| Toolbox | Trigger Keywords (examples) |
|---|---|
| **ProjectDiscovery** | layers, map, extent, active layer, this layer, selected |
| **DataInspection** | fields, columns, records, values, show me, metadata |
| **SelectionTools** | select, where, filter, within, clear, largest, top |
| **LayerStyling** | color, transparency, zoom, hide, show, opacity |
| **VectorProcessing** | buffer, clip, dissolve, merge, intersect, centroid |
| **RasterAnalysis** | slope, hillshade, DEM, raster, elevation |
| **ExportTools** | export, save, CSV, GeoJSON, PNG |

**Score-based routing**: if a query matches keywords from multiple toolboxes, each gets a score (= number of keywords matched). Only the top-scoring toolbox(es) are loaded. An intent override adjusts scores: `"show me / what are"` boosts DataInspection; `"select / pick"` boosts SelectionTools.

### Layer Resolution — `_resolve_layer(name)`

When a tool needs to find a layer by name, the resolution goes through 3 steps:

1. **Exact match** (case-insensitive) — returns immediately if unique
2. **Substring match** — if multiple layers contain the name, the **Ambiguity Card** is shown with clickable layer links
3. **Fuzzy match** — normalized alphanumeric comparison as a last resort

---

## 📖 Prompt Examples

AtQuery supports a wide range of GIS tasks. Most have been tested and you are welcome to report missing tools or request prompt updates.

### 🔍 Project Discovery & Data Inspection
- *"What layers are currently in my map?"*
- *"Tell me about the GOVT_PRS layer."*
- *"What is the coordinate system of the DCD layer?"*
- *"What fields does the DCD layer have?"*
- *"Show me the first 5 records of the DCD layer."*
- *"What are the columns and some example values for GOVT_PRS?"*
- *"Show me the top 5 largest areas in DCD sorted by SHAPE_Area descending."*
- *"Show me records from GOVT_PRS where NAME_EN contains 'Central'."*

### 🎯 Selection & Filtering
- *"Select the 5 largest areas in the DCD layer based on SHAPE_Area."*
- *"Select all features in DCD where SHAPE_Area > 1000000."*
- *"Select all schools in GOVT_PRS where NAME_EN starts with 'A'."*
- *"Select points in GOVT_PRS that are inside the DCD layer."*
- *"Clear all selections."*

### 🎨 Layer Styling & Canvas
- *"Change the color of the GOVT_PRS layer to red."*
- *"Set the transparency of the DCD layer to 50%."*
- *"Zoom to the extent of the DCD layer."*
- *"Make the DCD layer fully opaque again."*
- *"Hide the GOVT_PRS layer."*

### ⚙️ Vector Analysis
- *"Buffer the selected schools by 500 meters."*
- *"Clip the DCD layer using the current selection in GOVT_PRS."*
- *"Extract the selected features from the DCD layer into a new layer."*
- *"Find the intersection of DCD and GOVT_PRS."*
- *"Create centroids for the DCD layer."*
- *"Dissolve all features in the DCD layer."*
- *"Reproject the GOVT_PRS layer to WGS84."*

### 🏔️ Raster Analysis
> Requires a DEM/raster layer loaded in the project.
- *"Calculate the slope of the elevation layer."*
- *"Generate a hillshade for the DEM."*

### 💾 Export
- *"Export the GOVT_PRS layer as a CSV file."*
- *"Save the DCD layer as a GeoJSON."*
- *"Save the current map view as a PNG image."*

---

## 🛠️ Installation & Setup

### 1. Plugin Installation
1. Download or clone this repository.
2. Copy the folder into your QGIS plugins directory:
   - **Windows**: `%AppData%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable **AtQuery** in the Plugin Manager.

### 2. AI Backend (Ollama)
AtQuery requires **Ollama** running locally as the inference engine.
1. Download and install [Ollama](https://ollama.com).
2. Pull the default model:
   ```bash
   ollama run qwen2.5:3b
   ```
3. Ensure Ollama is running at `http://localhost:11434` before launching the plugin.

---

## 🏗️ Project Structure

```
AtQuery/
├── atquery.py                   ← Plugin entry point
├── ui/
│   ├── AtQuery_dockwidget.py    ← All UI logic, agentic loop, tool execution
│   └── AtQuery_input.py         ← Custom drag-and-drop QLineEdit
├── core/
│   ├── ai_brain.py              ← Keyword routing, system prompt, toolbox parser
│   ├── toolbox.md               ← Keyword → toolbox mapping catalog
│   ├── community_toolbox.json   ← User-extensible tool registry (auto-generated)
│   └── toolboxes/
│       ├── ProjectDiscovery.md  ← List layers, metadata, extent, active layer
│       ├── DataInspection.md    ← Fields, records, sample data, CRS
│       ├── SelectionTools.md    ← Expression, spatial, advanced selection
│       ├── VectorProcessing.md  ← Buffer, clip, dissolve, merge, reproject, etc.
│       ├── LayerStyling.md      ← Color, transparency, zoom, visibility
│       ├── RasterAnalysis.md    ← Slope, hillshade, aspect, clip by mask
│       └── ExportTools.md       ← Export to file, export canvas
└── TEST_SUITE.md                ← Full functional test scenarios
```

---

## 👤 Credits & Support

**AtQuery** was created by **Adela C**.
- **Issues**: Report bugs or request features to adelacky.de@gmail.com

*Transforming GIS from a tool you operate into a partner you converse with.*
