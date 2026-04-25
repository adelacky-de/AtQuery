# AtQuery: AI-Powered QGIS Agent

AtQuery is a QGIS plugin that brings the power of Large Language Models (LLMs) directly into your GIS workflow. It translates natural language instructions into precise PyQGIS commands and geoprocessing tasks using a local Ollama server.

## 🚀 Key Features

- **Natural Language Control**: Query your layers, filter attributes, and run spatial analysis using plain English.
- **Privacy-First (Local AI)**: Powered by [Ollama](https://ollama.com/), all data stays on your machine. No cloud dependencies or API keys required.
- **Skilling Framework**: Uses a dynamic **Toolbox** system. The AI identifies and loads only the necessary skills for your request, maximizing efficiency and reasoning accuracy.
- **High Performance**: Optimized for Apple Silicon (M1/M2/M3/M4/M5) using the **`qwen2.5:3b`** model for rapid reasoning and low memory overhead.
- **Interactive Chat**: A docked panel within QGIS for seamless interaction.

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

- **Discovery**: "What layers do I have in my project?"
- **Filtering**: "Select all districts with population over 50,000."
- **Styling**: "Make the 'roads' layer red."
- **Analysis**: "Create a 500-meter buffer around the hospitals layer."
- **Spatial Queries**: "Which points of interest are inside the 'Central' district?"

## 🔒 Security & Safety

AtQuery includes a security layer that restricts dangerous commands (e.g., file deletion or database dropping). However, it is always recommended to work on data backups when performing complex geoprocessing tasks.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
