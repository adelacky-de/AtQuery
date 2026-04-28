#AtQuery_dockwidget.oy

import requests
import json
import traceback
import os
import tempfile
import time
import re
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

from ..core.ai_brain import get_base_tools, get_toolbox_skills, get_system_prompt, identify_toolboxes

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
        
        # Resolve logo path
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))
        self.logo_path = os.path.join(self.plugin_dir, "resources", "Icon_AtQuery.jpg")
        
        self.main_widget = QtWidgets.QWidget()
        self.layout_stack = QtWidgets.QStackedLayout(self.main_widget)
        self.setWidget(self.main_widget)
        
        self._setup_ollama_status_view()
        self._setup_chat_view()
        self.check_ollama_status()
        
        # Set Window Icon
        self.setWindowIcon(QtWidgets.QIcon(self.logo_path))
        
    def set_iface(self, iface):
        self.iface = iface
        
    def _setup_ollama_status_view(self):
        self.ollama_status_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ollama_status_widget)
        
        # Logo + Title
        title_layout = QtWidgets.QHBoxLayout()
        logo_label = QtWidgets.QLabel()
        logo_pix = QtWidgets.QPixmap(self.logo_path).scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pix)
        title_label = QtWidgets.QLabel("<h1><span style='color: #4CAF50;'>AtQuery</span></h1>")
        title_layout.addStretch()
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        subtitle = QtWidgets.QLabel("<h3>Setup Required</h3>")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        
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
        
        layout.addLayout(title_layout)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(message)
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
        
        # Welcome with Logo
        welcome_html = f"""
        <div style='text-align: center; margin-bottom: 10px;'>
            <img src='{self.logo_path}' width='50' height='50'><br>
            <b style='font-size: 16px; color: #4CAF50;'>AtQuery by Adela C</b><br>
            <i>Your Agentic GIS Assistant</i>
        </div>
        <hr>
        Welcome! Ask a question about your QGIS project.<br>
        (e.g., 'What layers are in the project?')<br>
        """
        self.chat_display.setHtml(welcome_html)
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
        
        # Pre-load toolboxes based on keywords to save a turn
        detected = identify_toolboxes(user_text)
        for tb in detected:
            skills = get_toolbox_skills(tb)
            if skills:
                active_tools.extend(skills)
        
        try:
            for step in range(5): # Limit to 5 steps per turn
                # Limit context to last 6 messages (3 turns) + current turn to keep it FAST
                combined_history = self.conversation_history[-6:] + current_turn_history
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
                self.handle_ai_response("Operation finished (maximum steps reached).")
            self.conversation_history.extend(current_turn_history)
        except Exception as e:
            self.chat_display.append(f"<br><b>Error:</b> {str(e)}")
        finally:
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.user_input.setFocus()

    def _get_ai_response(self, messages, tools):
        # Concise sanitization
        sanitized = []
        for m in messages:
            nm = m.copy()
            if m.get('role') == 'assistant' and m.get('content'):
                nm['content'] = re.sub(r'^(AtQuery|User|Answer|Response|Thought|Assistant):\s*', '', m['content'], flags=re.I).strip()
            sanitized.append(nm)

        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": get_system_prompt()}] + sanitized,
            "tools": tools,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 400} # Lower temp for speed/consistency
        }
        
        try:
            resp = requests.post(self.ollama_url, json=payload, timeout=60)
            resp.raise_for_status()
            msg = resp.json().get('message', {})
            content = msg.get('content', '')
            if '{' in content:
                try:
                    start, end = content.find('{'), content.rfind('}') + 1
                    data = json.loads(content[start:end])
                    if 'content' in data: msg['content'] = data['content']
                    if 'suggested_queries' in data: msg['suggested_queries'] = data['suggested_queries']
                    if 'tool_calls' in data:
                        normalized = []
                        for c in data['tool_calls']:
                            f = c.get('function', c)
                            normalized.append({
                                "id": c.get('id', f"call_{time.time_ns()}"),
                                "type": "function",
                                "function": {"name": str(f.get('name', '')), "arguments": f.get('arguments', f.get('parameters', {}))}
                            })
                        msg['tool_calls'] = normalized
                except: pass
            return msg
        except Exception as e: raise Exception(f"Ollama Error: {e}")

    def handle_tool_call(self, tool_call_json):
        try:
            tc = json.loads(tool_call_json)
            func = tc.get("function", {})
            name, args = func.get("name"), func.get("arguments", {})
            
            # Special case for core management tools
            if name == 'load_toolbox_skills':
                return json.dumps(get_toolbox_skills(args.get('toolbox_name')))
            
            # Dynamic Execution for all other tools
            from ..core.ai_brain import get_implementation
            code = get_implementation(name)
            
            if code:
                # Prepare context for the dynamic code
                local_context = {
                    'self': self,
                    'args': args,
                    'QgsProject': QgsProject,
                    'QgsRectangle': QgsRectangle,
                    'QgsGeometry': QgsGeometry,
                    'QgsFeature': QgsFeature,
                    'QgsFields': QgsFields,
                    'processing': processing,
                    'json': json,
                    'result': None
                }
                
                # Execute the implementation code from Markdown
                exec(code, globals(), local_context)
                
                # Retrieve the result set by the code
                return json.dumps(local_context['result']) if local_context['result'] is not None else json.dumps({"status": "success"})
            
            return json.dumps({"error": f"Implementation for tool '{name}' not found."})
            
        except Exception as e:
            QgsMessageLog.logMessage(f"AtQuery Error: {traceback.format_exc()}", "AtQuery")
            return json.dumps({"error": str(e)})

    def _resolve_layer(self, name):
        if not name: return None
        all_layers = list(QgsProject.instance().mapLayers().values())
        
        # 1. Try exact match
        matches = QgsProject.instance().mapLayersByName(name)
        if matches: return matches[0]
        
        # 2. Normalize and try Exact Normalized Match
        def normalize(s):
            return re.sub(r'[^a-z0-9]', '', s.lower())
        
        target = normalize(name)
        if not target: return None
        
        for layer in all_layers:
            if normalize(layer.name()) == target:
                return layer
                
        # 3. Best "Contains" Match (Prioritize original layers over buffers/bboxes)
        potential_matches = []
        for layer in all_layers:
            layer_norm = normalize(layer.name())
            if target in layer_norm:
                # Rank by how close the name is to the target
                score = len(layer_norm) - len(target)
                # Penalize memory layers (likely outputs of previous steps)
                if layer.dataProvider().name() == 'memory':
                    score += 100
                potential_matches.append((score, layer))
        
        if potential_matches:
            # Return the match with the lowest score (closest name, non-memory preferred)
            potential_matches.sort(key=lambda x: x[0])
            return potential_matches[0][1]
            
        return None

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