# AtQuery: AI-Powered QGIS Agent
**Created by Adela C**

AtQuery is a next-generation QGIS plugin that integrates Large Language Models (LLMs) directly into the GIS workspace. By transforming natural language into executable PyQGIS logic, AtQuery allows users to perform complex spatial analysis, data inspection, and geoprocessing through a simple, conversational interface—all powered by a private, local Ollama server.

## 🚀 Key Features

- **Natural Language Control**: Query layers, filter attributes, and run spatial analysis using plain English.
- **Dictionary-Style Toolbox**: Uses a modular, keyword-indexed system. The AI identifies the correct GIS "Handbook" (Toolbox) and loads only the specific skills needed, optimizing reasoning for small models like `qwen2.5:3b`.
- **Proactive Fallback Loop**: If the AI is uncertain, it proactively asks: *"Do you want to [action]?"*. It executes only after your confirmation (**"Y/YES"**), ensuring safety and precision.
- **Expanded GIS Library**: Supports Vector processing, **Raster Analysis** (Slope, Hillshade), **Web Services** (WMS/WFS/XYZ Tiles), and **Terrain Analysis** (TIN, Contours).
- **Privacy-First (Local AI)**: Powered by [Ollama](https://ollama.com/), all data stays on your machine.
- **High Performance**: Optimized for rapid reasoning with low memory overhead.

## 🛠️ Installation

### 1. Requirements
- QGIS 3.x or later.
- [Ollama](https://ollama.com/) installed and running.

### 2. Pull the Optimized Model
Open your terminal and run:
```bash
ollama pull qwen2.5:3b
```

### 3. Install the Plugin
1. Download the AtQuery repository.
2. Place the `atquery` folder into your QGIS plugins directory:
   - **Windows**: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins`
   - **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
3. Restart QGIS or use the "Plugin Reloader" to enable **AtQuery**.

## 📖 Usage Examples

- **Discovery**: "What layers are in the project?"
- **Filtering**: "Select districts where NAME_EN is 'Southern'."
- **Analysis**: "Calculate slope from my elevation raster."
- **Web Data**: "Add the OpenStreetMap basemap."
- **3D/Terrain**: "Create a TIN interpolation for the points layer."

## 🧪 Testing & Metrics

You can run the automated self-test suite to verify the AI's reasoning and performance:
```bash
python3 test/test_brain_local.py --verbose
```
This will output a detailed dashboard including **Run Time**, **Keywords Identified**, **Toolbox Selected**, and **AI Reasoning Steps**.

## 🔒 Security & Safety

AtQuery includes a security layer that restricts dangerous commands (e.g., file deletion). The proactive fallback loop also ensures the AI confirms intent before executing significant geoprocessing tasks.

## 📄 License

This project is licensed under the MIT License.
