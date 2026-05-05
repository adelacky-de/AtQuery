# AtQuery_dockwidget.py

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

from ..core.ai_brain import (
    get_base_tools, get_toolbox_skills, get_system_prompt, get_forced_execution_prompt,
    identify_toolboxes, identify_community_toolbox, load_community_toolbox,
    get_available_toolboxes_summary
)

class AtQueryDockWidget(QtWidgets.QDockWidget):
    closingPlugin = QtCore.pyqtSignal()

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
        <div style='text-align: left; margin-bottom: 10px;'>
            <img src='file://{self.logo_path}' width='50' height='50'><br>
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
        self.chat_display.append("<i>AtQuery is thinking...</i>")
        QtWidgets.QApplication.processEvents()
        
        current_turn_history = [{"role": "user", "content": user_text}]
        active_tools = get_base_tools()
        
        # Pre-load built-in toolboxes by keyword match
        detected = identify_toolboxes(user_text)
        for tb in detected:
            skills = get_toolbox_skills(tb)
            if skills: active_tools.extend(skills)
        
        # Pre-load community toolbox keyword matches
        community_matches = identify_community_toolbox(user_text)
        if community_matches:
            active_tools.extend(community_matches)
        
        tool_was_executed = False
        gis_tools_called = set()  # Tracks real QGIS tools (excludes meta tools)
        META_TOOLS = {"load_toolbox_skills"}  # Tools that manage the loop, not QGIS actions

        try:
            for step in range(5):
                # FIX: Limit long-term memory to last 2 turns to prevent hallucination
                combined_history = self.conversation_history[-2:] + current_turn_history
                ai_msg = self._get_ai_response(combined_history, active_tools)
                current_turn_history.append(ai_msg)

                if not ai_msg.get("tool_calls"):
                    content = ai_msg.get("content", "").strip()
                    # Only mark executed if a real GIS tool already ran this turn
                    if gis_tools_called:
                        if not content:
                            content = "Action completed successfully."
                        elif "completed" not in content.lower() and "success" not in content.lower() and "failed" not in content.lower() and "error" not in content.lower():
                            content += "<br><br>✅ <b>Task completed.</b>"
                    
                    if content:
                        self.handle_ai_response(content, ai_msg.get("suggested_queries"))
                    break

                tool_outputs = []
                for tc in ai_msg["tool_calls"]:
                    output = self.handle_tool_call(json.dumps(tc))
                    tool_name = tc.get("function", {}).get("name", "")
                    if tool_name == "load_toolbox_skills":
                        skills = json.loads(output)
                        if isinstance(skills, list): active_tools.extend(skills)
                    else:
                        # A real QGIS tool was called
                        gis_tools_called.add(tool_name)
                    tool_outputs.append({"role": "tool", "content": output, "tool_call_id": tc.get("id")})
                current_turn_history.extend(tool_outputs)

            tool_was_executed = bool(gis_tools_called)
            
            # ── POST-LOOP FALLBACK ──────────────────────────────────────────
            if not tool_was_executed:
                self._handle_no_skill_fallback(user_text, current_turn_history)
            else:
                # FIX: Save only clean text to prevent tool JSON logs from confusing the AI
                final_ai_msg = [m for m in current_turn_history if m["role"] == "assistant" and m.get("content")]
                if final_ai_msg:
                    self.conversation_history.append({"role": "user", "content": user_text})
                    self.conversation_history.append({"role": "assistant", "content": final_ai_msg[-1]["content"]})

        except Exception as e:
            self.chat_display.append(f"<br><b>Error:</b> {str(e)}")

    def _handle_no_skill_fallback(self, query: str, current_turn_history: list):
        """
        Called when the 5-step loop finishes without executing any tool.
        Tier 1: Check community toolbox (already done in _send_query pre-load).
        Tier 2: Show specific confirm dialog — list available toolboxes.
        Tier 3: Y → direct force execute; N → LLM synthesis + community register.
        """
        from ..core.ai_brain import get_base_tools, _load_catalog_from_md, get_toolbox_skills
        from ..core.web_search import synthesize_and_register

        # Build the specific dialog message
        toolboxes_summary = get_available_toolboxes_summary()
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("AtQuery — No Matching Skill Found")
        msg_box.setIcon(QtWidgets.QMessageBox.Question)
        msg_box.setText(
            f"<b>No skill matched your request:</b><br><i>\"{query}\"</i><br><br>"
            f"AtQuery currently supports these toolboxes:<br>"
            f"<pre style='font-size:11px'>{toolboxes_summary}</pre>"
            f"<br>Is your request related to one of the above?"
        )
        yes_btn = msg_box.addButton("Yes — Execute Best Match", QtWidgets.QMessageBox.YesRole)
        no_btn  = msg_box.addButton("No — Search & Learn New Skill", QtWidgets.QMessageBox.NoRole)
        msg_box.exec_()

        if msg_box.clickedButton() == yes_btn:
            # ── Y: DIRECT FORCE EXECUTE ─────────────────────────────────────
            # Load ALL built-in toolboxes + community into a single tool set
            self.chat_display.append("<i>⚡ Force-loading all toolboxes and executing best match...</i>")
            QtWidgets.QApplication.processEvents()

            catalog = _load_catalog_from_md()
            forced_tools = get_base_tools()
            for tb_name in catalog.keys():
                forced_tools.extend(get_toolbox_skills(tb_name))
            forced_tools.extend(load_community_toolbox())

            # Single forced-execution AI call with specialized prompt
            try:
                payload_messages = [
                    {"role": "system", "content": get_forced_execution_prompt()},
                    {"role": "user",   "content": query}
                ]
                ai_msg = self._get_ai_response(payload_messages, forced_tools)

                if ai_msg.get("tool_calls"):
                    tool_outputs = []
                    for tc in ai_msg["tool_calls"]:
                        output = self.handle_tool_call(json.dumps(tc))
                        tool_outputs.append({"role": "tool", "content": output, "tool_call_id": tc.get("id")})
                    # Get final summary from AI
                    final_messages = payload_messages + [ai_msg] + tool_outputs
                    final_msg = self._get_ai_response(final_messages, forced_tools)
                    content = final_msg.get("content", "Best-match execution completed.")
                else:
                    content = ai_msg.get("content", "I executed the closest available skill.")
                
                self.handle_ai_response(content)
                current_turn_history.extend([ai_msg])
            except Exception as e:
                self.chat_display.append(f"<br><b>Force-execute error:</b> {str(e)}")

        else:
            # ── N: SYNTHESIZE + REGISTER NEW TOOL ──────────────────────────
            self.chat_display.append(
                "<i>🔍 No existing match. Synthesizing a new skill from AI knowledge...</i>"
            )
            QtWidgets.QApplication.processEvents()

            tool_data = synthesize_and_register(query)

            if tool_data:
                self.chat_display.append(
                    f"<br>✅ <b>New skill learned:</b> <code>{tool_data['name']}</code><br>"
                    f"<i>{tool_data['description']}</i><br>"
                    f"📧 Developer notified (via Formspree webhook).<br>"
                    f"🗂️ Saved to <code>community_toolbox.json</code> for future use."
                )
                # Now execute the newly synthesized tool immediately
                try:
                    from ..core.ai_brain import SKILL_IMPLEMENTATIONS
                    impl_code = SKILL_IMPLEMENTATIONS.get(tool_data['name'])
                    if impl_code:
                        local_context = {
                            'self': self, 'args': {}, 'QgsProject': __import__('qgis.core', fromlist=['QgsProject']).QgsProject,
                            'processing': __import__('processing'), 'json': json, 'result': None,
                            'iface': self.iface, 'canvas': self.iface.mapCanvas()
                        }
                        exec(impl_code, globals(), local_context)
                        r = local_context.get('result')
                        if r:
                            self.chat_display.append(f"<br>▶️ <b>Result:</b> {json.dumps(r)}")
                except Exception as ex:
                    self.chat_display.append(f"<br>⚠️ Skill saved but execution needs review: {str(ex)}")
            else:
                self.chat_display.append(
                    "<br>⚠️ Could not synthesize a skill for this request. "
                    "Please check your Ollama connection and try again."
                )

        # FIX: Save only clean text to prevent tool JSON logs from confusing the AI
        final_ai_msg = [m for m in current_turn_history if m["role"] == "assistant" and m.get("content")]
        if final_ai_msg:
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": final_ai_msg[-1]["content"]})
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
        # Remove 'Thinking...' indicator
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.select(QtGui.QTextCursor.BlockUnderCursor)
        if "AtQuery is thinking..." in cursor.selectedText():
            cursor.removeSelectedText()
        
        import re
        # Add space after periods if missing (e.g. "Sentence.Next sentence" -> "Sentence. Next sentence")
        text = re.sub(r'\.(?=[A-Za-z])', '. ', text)
        self.chat_display.append(f"<br>💡 <b>AtQuery:</b> {text}")
        if suggested:
            for q in suggested:
                self.chat_display.append(f" - <a href='#'>{q}</a>")

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
