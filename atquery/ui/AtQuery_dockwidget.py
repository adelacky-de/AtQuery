#AtQuery_dockwidget.oy

import requests
import json
import traceback
import os
import tempfile
import time
from datetime import datetime

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import QEvent

# Core QGIS imports
from qgis.core import (
    QgsProject,
    QgsMessageLog,
    QgsFeatureRequest,
    QgsVectorLayer,
    QgsGeometry,
    QgsRectangle,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsMapLayer
)
import processing 

from ..utils.installer_utils import (
    check_ollama_api,
    check_ollama_model_availability,
    get_os_info,
    get_installer_url,
    download_installer,
    launch_installer
)

from ..core.ai_brain import get_base_tools, get_toolbox_skills, get_system_prompt

# --- Installer Thread ---
class InstallerThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, url, file_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.file_path = file_path

    def run(self):
        success = download_installer(self.url, self.file_path, self.progress.emit)
        self.finished.emit(success, self.file_path)

# --- Main Dock Widget ---
class AtQueryDockWidget(QtWidgets.QDockWidget):
    
    closingPlugin = QtCore.pyqtSignal()
    PROGRESS_EVENT_TYPE = QEvent.Type(QEvent.User + 1)

    def _get_layer_by_name(self, layer_name):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() == layer_name:
                return layer
        return None

    def _run_processing_alg(self, algorithm_id, params):
        try:
            import processing
            dangerous_terms = ['delete', 'remove', 'drop', 'format', 'truncate', 'sql:execute']
            if any(term in algorithm_id.lower() for term in dangerous_terms):
                return json.dumps({"error": f"Security violation: Algorithm '{algorithm_id}' is restricted."})

            result = processing.run(algorithm_id, params)
            return json.dumps({"status": "success", "result": str(result)})
        except Exception as e:
            return json.dumps({"error": f"Algorithm '{algorithm_id}' failed: {str(e)}"})

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AtQuery AI Agent")
        self.iface = None 
        self.ollama_url = 'http://localhost:11434/api/chat'
        self.model_name = "qwen2.5:3b"
        self.conversation_history = []
        
        self.main_widget = QtWidgets.QWidget()
        self.layout_stack = QtWidgets.QStackedLayout(self.main_widget)
        self.setWidget(self.main_widget)
        
        self._setup_ollama_status_view()
        self._setup_chat_view()
        self.check_ollama_status()
        
    def set_iface(self, iface):
        self.iface = iface
        
    def _setup_ollama_status_view(self):
        self.ollama_status_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ollama_status_widget)
        title = QtWidgets.QLabel("<h1><span style='color: #4CAF50;'>AtQuery</span> Setup Required</h1>")
        title.setAlignment(QtCore.Qt.AlignCenter)
        message = QtWidgets.QLabel("<p>To use the AI Chat, you need to run the <a href='https://ollama.com'>Ollama</a> local LLM server.</p>")
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignCenter)
        message.setOpenExternalLinks(True)
        self.status_label = QtWidgets.QLabel("Status: Checking Ollama API...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.install_button = QtWidgets.QPushButton("Download Ollama Installer")
        self.install_button.clicked.connect(self._start_download)
        self.install_button.setStyleSheet("background-color: #007BFF; color: white; padding: 10px; font-weight: bold;")
        self.status_progress = QtWidgets.QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setVisible(False)
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addSpacing(20)
        layout.addWidget(self.status_label)
        layout.addWidget(self.status_progress)
        layout.addWidget(self.install_button)
        layout.addStretch(1)
        self.layout_stack.addWidget(self.ollama_status_widget)
        
    def _setup_chat_view(self):
        self.chat_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.chat_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setText("Welcome to AtQuery! Ask a question about your QGIS project.\n(e.g., 'What layers are in the project?')\n")
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("Enter your PyQGIS request...")
        self.user_input.returnPressed.connect(self._send_query)
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.clicked.connect(self._send_query)
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.user_input)
        input_layout.addWidget(self.send_button)
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
        self.layout_stack.addWidget(self.chat_widget)

    def check_ollama_status(self):
        if not check_ollama_api():
            self.layout_stack.setCurrentIndex(0)
            self.status_label.setText("Status: 🔴 Ollama API not found.")
            self.user_input.setEnabled(False)
            self.send_button.setEnabled(False)
            return
        if check_ollama_model_availability(self.model_name):
            self.layout_stack.setCurrentIndex(1)
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            self.layout_stack.setCurrentIndex(1)
            self.chat_display.append(f"🔴 Model '{self.model_name}' not found.")
            self.user_input.setEnabled(False)
            self.send_button.setEnabled(False)

    def _start_download(self):
        os_type = get_os_info()
        url = get_installer_url(os_type)
        if not url: return
        filename = 'Ollama-darwin.zip' if os_type == 'mac' else 'OllamaSetup.exe'
        file_path = os.path.join(tempfile.gettempdir(), filename)
        self.status_progress.setVisible(True)
        self.download_thread = InstallerThread(url, file_path)
        self.download_thread.progress.connect(self.status_progress.setValue)
        self.download_thread.finished.connect(self._download_finished)
        self.download_thread.start()

    def _download_finished(self, success, file_path):
        self.status_progress.setVisible(False)
        if success:
            launch_installer(file_path)

    # --- Chat Logic ---
    def _send_query(self):
        user_text = self.user_input.text().strip()
        if not user_text: return
        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        self.user_input.setEnabled(False)
        self.send_button.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

        if user_text.lower() in ["clear", "reset", "new chat"]:
            self.conversation_history = []
            self.chat_display.append("<br><i>History cleared.</i>")
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
            return

        current_turn_history = [{"role": "user", "content": user_text}]
        active_tools = get_base_tools()
        
        try:
            for step in range(10):
                combined_history = self.conversation_history[-10:] + current_turn_history
                ai_msg = self._get_ai_response(combined_history, active_tools)
                current_turn_history.append(ai_msg)

                if not ai_msg.get("tool_calls"):
                    self.handle_ai_response(ai_msg.get("content", ""), ai_msg.get("suggested_queries"))
                    break

                tool_outputs = []
                for tc in ai_msg["tool_calls"]:
                    output = self.handle_tool_call(json.dumps(tc))
                    if tc.get("function", {}).get("name") == "load_toolbox_skills":
                        try:
                            skills = json.loads(output)
                            if isinstance(skills, list): active_tools.extend(skills)
                        except: pass
                    tool_outputs.append({"role": "tool", "content": output, "tool_call_id": tc.get("id")})
                current_turn_history.extend(tool_outputs)
            else:
                self.handle_ai_response("Task timed out.")
            self.conversation_history.extend(current_turn_history)
        except Exception as e:
            self.chat_display.append(f"<br><b>Error:</b> {str(e)}")
        finally:
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.user_input.setFocus()

    def _get_ai_response(self, messages, tools):
        sanitized_messages = []
        prefixes = ["AtQuery:", "User:", "Answer:", "Response:", "Thought:", "Assistant:"]
        for msg in messages:
            new_msg = msg.copy()
            if msg.get('role') == 'assistant' and msg.get('content'):
                content = msg['content'].strip()
                for p in prefixes:
                    if content.lower().startswith(p.lower()): content = content[len(p):].strip()
                new_msg['content'] = content
            sanitized_messages.append(new_msg)

        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": get_system_prompt()}] + sanitized_messages,
            "tools": tools,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 500}
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=90)
            resp.raise_for_status()
            msg = resp.json().get('message', {})
            content = msg.get('content', '')
            if '{' in content:
                try:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    data = json.loads(content[start:end])
                    if 'content' in data: msg['content'] = data['content']
                    if 'suggested_queries' in data: msg['suggested_queries'] = data['suggested_queries']
                    if 'tool_calls' in data:
                        raw = data['tool_calls']
                        normalized = []
                        for c in raw:
                            func = c.get('function', c)
                            args = func.get('arguments', func.get('parameters', {}))
                            normalized.append({
                                "id": c.get('id', f"call_{time.time_ns()}"),
                                "type": "function",
                                "function": {"name": str(func.get('name', '')), "arguments": args}
                            })
                        msg['tool_calls'] = normalized
                except: pass
            return msg
        except Exception as e:
            raise Exception(f"Ollama Error: {e}")

    def handle_tool_call(self, tool_call_json):
        try:
            tc = json.loads(tool_call_json)
            func = tc.get("function", {})
            name = func.get("name")
            args = func.get("arguments", {})
            
            if name == 'get_toolbox_catalog':
                from ..core.ai_brain import _load_catalog_from_md
                catalog = _load_catalog_from_md()
                return json.dumps(catalog)
            elif name == 'load_toolbox_skills':
                return json.dumps(get_toolbox_skills(args.get('toolbox_name')))
            elif name == 'QgsProject_mapLayers':
                return json.dumps({"layers": [l.name() for l in QgsProject.instance().mapLayers().values()]})
            elif name == 'QgsVectorLayer_fields':
                layer = self._resolve_layer(args.get('layer_name'))
                if layer: return json.dumps({"fields": [f.name() for f in layer.fields()]})
                return json.dumps({"error": "Layer not found"})
            elif name == 'QgsVectorLayer_selectByExpression':
                layer = self._resolve_layer(args.get('layer_name'))
                if layer:
                    layer.selectByExpression(args.get('sql'))
                    if layer.selectedFeatureCount() > 0: self.iface.mapCanvas().zoomToSelected(layer)
                    return json.dumps({"status": "selected", "count": layer.selectedFeatureCount()})
            elif name == 'processing_run_native_buffer':
                layer = self._resolve_layer(args.get('layer_name'))
                if layer:
                    res = processing.run("native:buffer", {'INPUT': layer, 'DISTANCE': args.get('distance'), 'OUTPUT': 'memory:'})
                    QgsProject.instance().addMapLayer(res['OUTPUT'])
                    return json.dumps({"status": "success"})
            # ... other tools ...
            return json.dumps({"error": "Tool not implemented"})
        except Exception as e: return json.dumps({"error": str(e)})

    def _resolve_layer(self, name):
        if not name: return None
        matches = QgsProject.instance().mapLayersByName(name)
        return matches[0] if matches else None

    def handle_ai_response(self, text, suggested=None):
        cleaned = text.strip()
        # Detect if text is a dictionary index (contains lots of keywords)
        if "Toolbox" in cleaned and "Keywords" in cleaned:
            # Format as a simple HTML table for the chat
            lines = cleaned.split('\n')
            html = "<table border='1' style='border-collapse: collapse;'><tr><th>Toolbox</th><th>Keywords</th></tr>"
            for line in lines:
                if '|' in line and not '---' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 2:
                        html += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td></tr>"
            html += "</table>"
            cleaned = html

        self.chat_display.append(f"<br><b>AtQuery:</b> {cleaned}")
        if suggested:
            self.chat_display.append("<br><small style='color: #666;'><i>Suggested Queries:</i></small>")
            for q in suggested:
                self.chat_display.append(f"<br>• <a href='#' style='color: #007BFF;'>{q}</a>")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        super().closeEvent(event)