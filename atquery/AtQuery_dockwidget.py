#AtQuery_dockwidget.oy

import requests
import json
import traceback
import os
import tempfile

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import QEvent

# Core QGIS imports — only what we actually use
from qgis.core import (
    QgsProject,
    QgsMessageLog,
    QgsFeatureRequest   # ← Only this one is needed for filtering
)

from .installer_utils import (
    check_ollama_api,
    get_os_info,
    get_installer_url,
    download_installer,
    launch_installer
)

from .ai_brain import get_tools, get_system_prompt

# --- Installer Thread for Non-Blocking Download ---
class InstallerThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool, str) # success, output_path

    def __init__(self, url, file_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.file_path = file_path

    def run(self):
        success = download_installer(
            self.url, 
            self.file_path, 
            self.progress.emit
        )
        self.finished.emit(success, self.file_path)

# --- Main Dock Widget ---
class AtQueryDockWidget(QtWidgets.QDockWidget):
    
    closingPlugin = QtCore.pyqtSignal()
    PROGRESS_EVENT_TYPE = QEvent.Type(QEvent.User + 1)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AtQuery AI Agent")
        self.iface = None 
        self.download_thread = None
        
        # 1. Main Widget and Stacked Layout (for different states)
        self.main_widget = QtWidgets.QWidget()
        self.layout_stack = QtWidgets.QStackedLayout(self.main_widget)
        self.setWidget(self.main_widget)
        
        # 2. Setup the Ollama Status View (Index 0)
        self._setup_ollama_status_view()
        
        # 3. Setup the Chat Interface (Index 1)
        self._setup_chat_view()

        # Check API status immediately upon creation
        self.check_ollama_status()
        
    def set_iface(self, iface):
        """Allows the main plugin class to pass the QGIS interface."""
        self.iface = iface
        
    def _setup_ollama_status_view(self):
        """Creates the view displayed when Ollama is not running."""
        self.ollama_status_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.ollama_status_widget)
        
        title = QtWidgets.QLabel("<h1><span style='color: #4CAF50;'>AtQuery</span> Setup Required</h1>")
        title.setAlignment(QtCore.Qt.AlignCenter)
        
        message = QtWidgets.QLabel(
            "<p>To use the AI Chat, you need to run the <a href='https://ollama.com'>Ollama</a> local LLM server.</p>"
            "<p>Please ensure Ollama is installed and running, or use the installer below.</p>"
        )
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
        """Creates the primary chat interface."""
        self.chat_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.chat_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setText("Welcome to AtQuery! Ask a question about your QGIS project to get PyQGIS code.\n(e.g., 'What are the names of all the layers?')\n")
        
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

    # --- Ollama Handling ---
    def check_ollama_status(self):
        """Tries to connect to the Ollama API."""
        if check_ollama_api():
            self.layout_stack.setCurrentIndex(1) # Switch to chat view
            self.chat_display.append("<br>🟢 Ollama API Connected. Loading model...")
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            self.layout_stack.setCurrentIndex(0) # Switch to setup view
            self.status_label.setText("Status: 🔴 Ollama API not found (http://localhost:11434).")
            self.user_input.setEnabled(False)
            self.send_button.setEnabled(False)

    def _start_download(self):
        """Starts the download of the Ollama installer in a separate thread."""
        os_type = get_os_info()
        url = get_installer_url(os_type)
        
        if not url:
            self.status_label.setText("Error: Unsupported OS for direct download.")
            return

        # Use a temporary file path
        if os_type == 'mac':
            filename = 'Ollama-darwin.zip'
        else:
            filename = 'OllamaSetup.exe'
            
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        self.install_button.setEnabled(False)
        self.status_label.setText(f"Status: Downloading installer to {file_path}...")
        self.status_progress.setVisible(True)
        
        self.download_thread = InstallerThread(url, file_path)
        self.download_thread.progress.connect(self._update_progress)
        self.download_thread.finished.connect(self._download_finished)
        self.download_thread.start()

    def _update_progress(self, value):
        """Updates the progress bar during download."""
        self.status_progress.setValue(value)

    def _download_finished(self, success, file_path):
        """Handles the completion of the download thread."""
        self.status_progress.setVisible(False)
        self.install_button.setEnabled(True)
        
        if success:
            self.status_label.setText(f"Status: Download complete! Installer saved to {file_path}.")
            launch_success = launch_installer(file_path)
            if launch_success:
                self.status_label.setText("Status: Installer launched. Please follow the instructions to install Ollama.")
            else:
                self.status_label.setText(f"Status: Downloaded, but failed to launch installer. Please run: {file_path}")
        else:
            self.status_label.setText("Status: ❌ Download failed. Check your connection or download manually from ollama.com.")
            
    # --- Chat Logic ---
    def _send_query(self):
        """Processes the user's query — clean UI, no debug spam."""
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        self.user_input.setPlaceholderText("Thinking...")
        self.user_input.setEnabled(False)
        self.send_button.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

        try:
            # PHASE 1: Force tool call (AI asks for layer list)
            response_text, tool_call_json = self._get_ai_response(user_text)
            QgsMessageLog.logMessage(f"AtQuery Debug: Phase 1 - response_text: {response_text}, tool_call_json: {tool_call_json}", "AtQuery", 0)

            if tool_call_json:
                # Execute tool silently — no output to user
                tool_output = self.handle_tool_call(tool_call_json)
                QgsMessageLog.logMessage(f"AtQuery Debug: Phase 1 - tool_output: {tool_output}", "AtQuery", 0)

                # PHASE 2: Send real data back → AI gives beautiful final answer
                response_text, final_tool_call_json = self._get_ai_response(user_text, tool_output)
                QgsMessageLog.logMessage(f"AtQuery Debug: Phase 2 - response_text: {response_text}, final_tool_call_json: {final_tool_call_json}", "AtQuery", 0)

                if final_tool_call_json:
                    # If AI still returns a tool call in Phase 2, execute it
                    final_tool_output = self.handle_tool_call(final_tool_call_json)
                    QgsMessageLog.logMessage(f"AtQuery Debug: Phase 2 - final_tool_output: {final_tool_output}", "AtQuery", 0)
                    # The final display should reflect the outcome of this tool call, not just the response_text
                    # For now, we'll just display the response_text, but this might need refinement
                    self.handle_ai_response(response_text)
                else:
                    # Show only the final clean answer
                    self.handle_ai_response(response_text)
            else: # No tool call in Phase 1, direct answer (rare)
                self.handle_ai_response(response_text)

        except Exception as e:
            self.chat_display.append(f"<br>Error: Could not reach Ollama. Is it running?")
            QgsMessageLog.logMessage(f"AtQuery Error: {traceback.format_exc()}", "AtQuery", 2)

        finally:
            self.user_input.setPlaceholderText("Ask anything about your project...")
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)

    def handle_tool_call(self, tool_call_json):
        try:
            call = json.loads(tool_call_json)
            name = call['function']['name']
            args = call['function'].get('arguments', {})

            if name == 'get_layer_list':
                layers = QgsProject.instance().mapLayers().values()
                return json.dumps({"layers": [l.name() for l in layers]})

            elif name == 'get_layer_details':
                layer_name = args.get('layer_name')
                # Use the same fuzzy matching logic as for query_layer/select_features
                matching_layers = [l for l in QgsProject.instance().mapLayers().values() if layer_name.lower() in l.name().lower()]
                if not matching_layers:
                    return json.dumps({"error": f"Layer '{layer_name}' not found or no close match."})
                elif len(matching_layers) > 1:
                    return json.dumps({"error": f"Multiple layers found matching '{layer_name}': {[l.name() for l in matching_layers]}. Please be more specific."})
                else:
                    layer = matching_layers[0]
                
                fields = [field.name() for field in layer.fields()]
                return json.dumps({"layer_name": layer.name(), "fields": fields})

            elif name in ('query_layer', 'select_features'):
                layer_name = args.get('layer_name')
                sql = args.get('sql', '').strip()

                matching_layers = [l for l in QgsProject.instance().mapLayers().values() if layer_name.lower() in l.name().lower()]
                if not matching_layers:
                    return json.dumps({"error": f"Layer '{layer_name}' not found or no close match."})
                elif len(matching_layers) > 1:
                    return json.dumps({"error": f"Multiple layers found matching '{layer_name}': {[l.name() for l in matching_layers]}. Please be more specific."})
                else:
                    layer = matching_layers[0]
                if not layer:
                    return json.dumps({"error": "Layer not found"})

                # === BUILD A BULLETPROOF EXPRESSION ===
                # If user gave full SQL like "AREA_CODE = 'STH'", extract the condition
                condition = sql
                if sql.upper().startswith("SELECT"):
                    # Extract everything after WHERE
                    if "WHERE" in sql.upper():
                        condition = sql.split("WHERE", 1)[1].strip()
                # If just a condition like "AREA_CODE = 'STH'"
                # → Quote field name properly
                if '=' in condition and not condition.strip().startswith('"'):
                    field, value = [part.strip() for part in condition.split('=', 1)]
                    if not field.startswith('"'):
                        field = f'"{field}"'
                    condition = f'{field} = {value}'

                # Final safe expression
                expr = QgsExpression(condition)
                if expr.hasParserError():
                    return json.dumps({"error": f"Invalid expression: {expr.parserErrorString()}"})

                request = QgsFeatureRequest(expr)
                features = list(layer.getFeatures(request))
                count = len(features)

                # Select + zoom if requested
                if name == 'select_features':
                    layer.selectByIds([f.id() for f in features])
                    if count > 0:
                        self.iface.mapCanvas().zoomToSelected(layer)
                    action = "Selected and zoomed to"
                else:
                    action = "Found"

                return json.dumps({
                    "layer": layer_name,
                    "sql": condition,
                    "count": count,
                    "action": action
                })
            
        except Exception as e:
            return json.dumps({"error": str(e)})
        
    def _get_ai_response(self, prompt, tool_output=None):
        """
        Sends the request to the local Ollama server.
        Returns (response_text, tool_call_json).
        """
        model = "llama3.2:3b-instruct-q4_K_M" # Assuming this model is downloaded
        
        # Build the message history for the LLM
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # If we have tool output from a previous step, include it
        if tool_output is not None:
             messages.append({
                 "role": "tool",
                 "content": tool_output
             })

        # Tool calls are specified in the payload to enable function calling
        payload = {
            "model": model,
            "messages": messages,
            "system": get_system_prompt(),
            "tools": get_tools(),
            "stream": False # We need the full response at once
        }
        
        print(f"Ollama API Request Payload: {json.dumps(payload, indent=2)}")
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://localhost:11434/api/chat', headers=headers, json=payload)
        response.raise_for_status() # Raises an exception for bad status codes
        
        data = response.json()
        QgsMessageLog.logMessage(f"AtQuery Debug: Ollama Raw Response: {json.dumps(data, indent=2)}", "AtQuery", 0)
        
        # Check for tool call
        if 'tool_calls' in data['message']:
            QgsMessageLog.logMessage(f"AtQuery Debug: Tool calls detected in Ollama response.", "AtQuery", 0)
            # Ollama returns a list of tool calls. We only support one for now.
            tool_call = data['message']['tool_calls'][0]
            tool_call_json = json.dumps(tool_call)
            return data['message']['content'] if 'content' in data['message'] else "", tool_call_json
        else:
            # If no tool calls, it's an unexpected conversational response.
            # Log it as an error and return empty to force the AI to generate a tool call next turn.
            QgsMessageLog.logMessage(f"AtQuery Error: AI did not generate a tool call. Raw response: {data['message'].get('content', 'No content')}", "AtQuery", 2)
            return data['message'].get('content', 'No content'), None # Return content for debugging, but no tool call

    def handle_ai_response(self, response_text):
        """Displays the final AI answer with nice SQL code formatting."""
        if not response_text.strip():
            self.chat_display.append("<br><b>AtQuery:</b> No result.")
            return

        # Convert markdown ```sql ... ``` into styled HTML block
        lines = response_text.split('\n')
        formatted = response_text

        # Replace ```sql ... ``` with styled <pre> block
        in_code_block = False
        lines = formatted.split('\n')
        output_lines = []

        for line in lines:
            if line.strip().startswith('```sql'):
                output_lines.append('<pre style="background:#f4f4f4; padding:12px; border-radius:8px; font-family:Consolas,monospace; margin:10px 0;">')
                in_code_block = True
            elif line.strip() == '```':
                output_lines.append('</pre>')
                in_code_block = False
            elif in_code_block:
                output_lines.append(line)
            else:
                output_lines.append(line)

        final_html = "<br>".join(output_lines)

        # Final display
        self.chat_display.append(f"<br><b>AtQuery:</b> {final_html}")

    def execute_code(self, code_text):
            """Runs the PyQGIS code generated by the AI safely."""
            
            # 1. Clean up the code (AI often wraps code in markdown)
            clean_code = code_text.replace("```python", "").replace("```", "").strip()
            
            if not clean_code:
                self.chat_display.append("❌ AI returned empty code.")
                return

            self.chat_display.append(f"\n> AI CODE:\n{clean_code}")
            
            # 2. Use exec() to run the code in a controlled environment
            try:
                # Define the execution scope: all variables and functions available to the AI code
                # We override 'print' to redirect output back to the chat display
                execution_scope = {
                    'iface': self.iface,
                    'QgsProject': QgsProject,
                    'QgsMessageLog': QgsMessageLog,
                    # Redirect print() function output to the chat display
                    'print': lambda x: self.chat_display.append(f"[OUTPUT] {x}")
                }
                
                exec(clean_code, execution_scope)
                
                # IMPORTANT: Explicit success message to confirm action
                self.chat_display.append("\n✅ [SUCCESS: Selection/Action Executed]")
                
            except Exception as e:
                self.chat_display.append(f"\n❌ [EXECUTION ERROR] {type(e).__name__}: {str(e)}")
                QgsMessageLog.logMessage(f"PyQGIS Execution Error: {traceback.format_exc()}", 'AtQuery', 2)

    def closeEvent(self, event):
        """Handles the close event to emit a signal."""
        self.closingPlugin.emit()
        super().closeEvent(event)