# AtQuery: AI-Powered QGIS Agent
**Created by Adela C**

AtQuery is a next-generation QGIS plugin that integrates Large Language Models (LLMs) directly into the GIS workspace. By transforming natural language into executable PyQGIS logic, AtQuery allows users to perform complex spatial analysis, data inspection, and geoprocessing through a simple, conversational interface—all powered by a private, local Ollama server.

## 🚀 Key Features

- **Natural Language Control**: Query layers, filter attributes, and run spatial analysis using plain English.
- **Dynamic Skill Library**: Uses a modular, keyword-indexed system. The AI identifies the correct GIS "Handbook" (Toolbox) and loads only the specific skills needed.
- **Self-Executing Toolboxes**: Python implementation is stored directly in Markdown files, allowing the AI to execute complex GIS logic dynamically.
- **Proactive GIS Assistant**: Automatically zooms to selections, repaints layers, and handles multi-step reasoning.
- **Expanded GIS Library**: Supports Vector processing, **Raster Analysis**, **Web Services**, and **Terrain Analysis**.

## 🛠️ Installation

1. Clone or download this repository.
2. Copy the `atquery` folder to your QGIS plugins directory.
3. Ensure you have [Ollama](https://ollama.com) installed and running locally.
4. Download the `qwen2.5:3b` model: `ollama run qwen2.5:3b`.

## 📄 License

This project is licensed under the MIT License.
