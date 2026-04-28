#AtQuery_dockwidget.oy

import requests
import json
import traceback
import os
import tempfile
import time
import re
from datetime import datetime

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.core import QgsProject, QgsMessageLog, QgsRectangle, QgsGeometry, QgsFeature, QgsFields
from qgis.utils import iface
import processing

from ..core.ai_brain import get_base_tools, get_toolbox_skills, get_system_prompt, identify_toolboxes

class AtQueryDockWidget(QtWidgets.QDockWidget):
    def __init__(self, parent=None):
        super(AtQueryDockWidget, self).__init__(parent)
        self.setWindowTitle("AtQuery AI Agent")
        self.setObjectName("AtQueryDockWidget")
        
        self.ollama_url = "http://localhost:11434/api/chat"
        self.model_name = "qwen2.5:3b"
        self.conversation_history = []
        
        # Resolve logo path
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))
        self.logo_path = os.path.join(self.plugin_dir, "Icon_AtQuery.jpg")
        
        self.main_widget = QtWidgets.QWidget()
        self.layout_stack = QtWidgets.QStackedLayout(self.main_widget)
        self.setWidget(self.main_widget)
        
        self._setup_ollama_status_view()
        self._setup_chat_view()
        self.check_ollama_status()
        
        # Set Window Icon
        self.setWindowIcon(QtGui.QIcon(self.logo_path))

    def set_iface(self, iface):
        """Sets the QGIS interface reference."""
        self.iface = iface
        
    def _setup_ollama_status_view(self):
        self.ollama_status_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ollama_status_widget)
        
        title_layout = QtWidgets.QHBoxLayout()
        logo_label = QtWidgets.QLabel()
        logo_pix = QtGui.QPixmap(self.logo_path).scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
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
        
        self.install_button = QtWidgets.QPushButton("Download Ollama")
        self.install_button.setStyleSheet("background-color: #007BFF; color: white; padding: 10px;")
        
        layout.addLayout(title_layout)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(message)
        layout.addWidget(self.status_label)
        layout.addWidget(self.install_button)
        layout.addStretch(1)
        self.layout_stack.addWidget(self.ollama_status_widget)
        
    def _setup_chat_view(self):
        self.chat_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.chat_widget)
        
        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        
        welcome_html = f"""
        <div style='text-align: center; margin-bottom: 10px;'>
            <img src='{self.logo_path}' width='50' height='50'><br>
            <b style='font-size: 16px; color: #4CAF50;'>AtQuery by Adela C</b><br>
            <i>Your Agentic GIS Assistant</i>
        </div>
        <hr>
        Welcome! Ask a question about your QGIS project.<br>
        """
        self.chat_display.setHtml(welcome_html)
        
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setPlaceholderText("Enter request...")
        self.user_input.returnPressed.connect(self._send_query)
        
        layout.addWidget(self.chat_display)
        layout.addWidget(self.user_input)
        self.layout_stack.addWidget(self.chat_widget)

    def check_ollama_status(self):
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
            self.layout_stack.setCurrentWidget(self.chat_widget)
        except:
            self.layout_stack.setCurrentWidget(self.ollama_status_widget)

    def _send_query(self):
        user_text = self.user_input.text().strip()
        if not user_text: return
        
        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        
        current_turn_history = [{"role": "user", "content": user_text}]
        active_tools = get_base_tools()
        
        # Pre-load based on keywords
        detected = identify_toolboxes(user_text)
        for tb in detected:
            skills = get_toolbox_skills(tb)
            if skills: active_tools.extend(skills)
        
        try:
            for step in range(5):
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
                        skills = json.loads(output)
                        if isinstance(skills, list): active_tools.extend(skills)
                    tool_outputs.append({"role": "tool", "content": output, "tool_call_id": tc.get("id")})
                current_turn_history.extend(tool_outputs)
            
            self.conversation_history.extend(current_turn_history)
        except Exception as e:
            self.chat_display.append(f"<br><b>Error:</b> {str(e)}")

    def _get_ai_response(self, messages, tools):
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
            "options": {"temperature": 0.0, "num_predict": 400}
        }
        
        resp = requests.post(self.ollama_url, json=payload, timeout=60)
        resp.raise_for_status()
        msg = resp.json().get('message', {})
        
        # Attempt to repair JSON if AI puts it in content
        content = msg.get('content', '')
        if '{' in content:
            try:
                start, end = content.find('{'), content.rfind('}') + 1
                data = json.loads(content[start:end])
                if 'content' in data: msg['content'] = data['content']
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

    def handle_tool_call(self, tool_call_json):
        try:
            tc = json.loads(tool_call_json)
            func = tc.get("function", {})
            name, args = func.get("name"), func.get("arguments", {})
            
            if name == 'load_toolbox_skills':
                return json.dumps(get_toolbox_skills(args.get('toolbox_name')))
            
            from ..core.ai_brain import get_implementation
            code = get_implementation(name)
            if code:
                local_context = {
                    'self': self, 'args': args, 'QgsProject': QgsProject, 
                    'QgsRectangle': QgsRectangle, 'QgsGeometry': QgsGeometry, 
                    'QgsFeature': QgsFeature, 'QgsFields': QgsFields,
                    'processing': processing, 'json': json, 'result': None,
                    'iface': self.iface, 'canvas': self.iface.mapCanvas()
                }
                exec(code, globals(), local_context)
                return json.dumps(local_context['result']) if local_context['result'] is not None else json.dumps({"status": "success"})
            
            return json.dumps({"error": f"Tool '{name}' implementation not found."})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _resolve_layer(self, name):
        if not name: return None
        all_layers = list(QgsProject.instance().mapLayers().values())
        matches = QgsProject.instance().mapLayersByName(name)
        if matches: return matches[0]
        
        def normalize(s): return re.sub(r'[^a-z0-9]', '', s.lower())
        target = normalize(name)
        if not target: return None
        
        potential = []
        for layer in all_layers:
            ln = normalize(layer.name())
            if target in ln:
                score = len(ln) - len(target)
                if layer.dataProvider().name() == 'memory': score += 100
                potential.append((score, layer))
        
        if potential:
            potential.sort(key=lambda x: x[0])
            return potential[0][1]
        return None

    def handle_ai_response(self, text, suggested=None):
        self.chat_display.append(f"<br><b>AtQuery:</b> {text}")
        if suggested:
            for q in suggested:
                self.chat_display.append(f" - <a href='#'>{q}</a>")
