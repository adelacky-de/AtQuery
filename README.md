# 🌍 AtQuery: The Agentic QGIS Assistant

**AtQuery** is a QGIS plugin that brings the Agentic AI directly to your geospatial workspace. By bridging the gap between natural language and **PyQGIS**, AtQuery allows you to query, analyze, and automate GIS workflows without writing a single line of code.

---

## 🚀 Key Features

- **Natural Language GIS**: No more searching through menus and the toolbox. Ask QGIS questions like "Buffer the parks by 100m."
*   **Agentic Reasoning **: Powered by a dynamic tool-calling loop. The AI analyses your query, extract the keywords, checks your layers, inspects their attributes, and chooses the right GIS tool autonomously.
*   **Local & Private**: Runs entirely on your machine using **Ollama**. Your data never leaves your computer, ensuring total privacy and zero API costs.
*   **Modular Skill Library**: Capabilities are organized into "Toolboxes" (Markdown files). The system only loads the skills relevant to your specific request.
*   **Self-Expanding Skill Library (Online Search)**: If AtQuery lacks a built-in skill, click "Search & Learn New Skill" to let the AI automatically synthesize a new QGIS tool from its knowledge and save it to your local `community_toolbox.json` store for future use.
*   **Live Code Execution**: See the AI's generated PyQGIS code in real-time. It's not just an assistant; it's a way to learn PyQGIS.

---

## 📖 Prompt Examples

AtQuery can handle a wide variety of tasks. Most of the queries have been tested but not all. Below are some things you can try, and you are welcome to tell me to update the missing tools or the prompt as needed.

### 🔍 Project Discovery & Data Inspection
- *"List all the layers in my map."*
- *"What are the attribute fields in the 'Counties' layer?"*
- *"Show me the coordinate system of the active layer."*

### 🎯 Selection & Filtering
- *"Select all buildings with more than 5 floors in the 'structures' layer."*
- *"Filter the 'Rivers' layer to only show the ones with 'Danube' in the name."*
- *"Find all parcels that intersect with the current selection."*

### 🎨 Layer Styling
- *"Change the color of the 'Forests' layer to dark green."*
- *"Set the transparency of the 'Satellite' layer to 50%."*

### ⚙️ Vector & Raster Analysis
- *"Create a 500-meter buffer around the selected bus stops."*
- *"Calculate the slope from the 'DEM' raster layer."*
- *"Clip the 'roads' layer using the 'boundary' polygon."*
- *"Join the 'demographics' table to the 'counties' layer using an Inner Join."*
- *"Extract features from the 'parcels' layer where 'Zoning' = 'Commercial'."*
- *"Create a TIN interpolation surface from the elevation points layer."*

### 💾 Export & Map Canvas
- *"Export the 'buildings' layer to a GeoJSON file."*
- *"Save the 'roads' layer as a PostgreSQL / PostGIS database file."*
- *"Save the current map view as a PNG image."*
- *"Zoom the map to coordinate 114.1, 22.3."*

---

## 🛠️ Installation & Setup

### 1. Plugin Installation
1.  Download or clone this repository.
2.  Copy the folder into your QGIS plugins directory:
    - **Windows**: `%AppData%\QGIS\QGIS3\profiles\default\python\plugins\`
    - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
    - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3.  Restart QGIS and enable **AtQuery** in the Plugin Manager.

### 2. AI Backend (Ollama)
AtQuery requires **Ollama** to be running locally as the inference engine.
1.  Download and install [Ollama](https://ollama.com).
2.  Pull the default model (AtQuery is optimized for Qwen 2.5):
    ```bash
    ollama run qwen2.5:3b
    ```
3.  Ensure Ollama is running (`http://localhost:11434`) before launching the plugin.

---

## 🏗️ Technical Architecture

AtQuery uses a **Dynamic Skill Library** architecture:
- **`core/toolbox.md`**: The master catalog of all available skillsets.
- **`core/toolboxes/`**: Modular Markdown files containing tool schemas (JSON) and their PyQGIS implementations.
- **Agent Loop**: When you type a query, the agent identifies the required toolbox, loads the specific functions into its memory, and executes them in a multi-step reasoning loop.

---

## 👤 Credits & Support

**AtQuery** was created by **Adela C**. 
- **Issues**: Report bugs or request features to adelacky.de@gmail.com

*Transforming GIS from a tool you operate into a partner you converse with.*
