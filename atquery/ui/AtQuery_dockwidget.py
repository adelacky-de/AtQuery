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

# Core QGIS imports — only what we actually use
from qgis.core import (
    QgsProject,
    QgsMessageLog,
    QgsFeatureRequest,   # ← Only this one is needed for filtering
    QgsVectorLayer,      # For creating new layers
    QgsGeometry,         # For spatial operations
    QgsRectangle,        # For bounding boxes
    QgsFeature,          # For creating features
    QgsField,            # For layer fields
    QgsFields            # For field collections
)
import processing # Import processing separately as it's not directly in qgis.core

from ..utils.installer_utils import (
    check_ollama_api,
    check_ollama_model_availability,
    get_os_info,
    get_installer_url,
    download_installer,
    launch_installer
)

from ..core.ai_brain import get_tools, get_system_prompt

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
        self.ollama_url = 'http://localhost:11434/api/chat'
        self.model_name = "llama3.2:3b-instruct-q4_K_M" # Reverted to user's preferred model
        self.conversation_history = []
        
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
        """Tries to connect to the Ollama API and checks for the required model."""
        if not check_ollama_api():
            self.layout_stack.setCurrentIndex(0) # Switch to setup view
            self.status_label.setText("Status: 🔴 Ollama API not found (http://localhost:11434).")
            self.user_input.setEnabled(False)
            self.send_button.setEnabled(False)
            return

        # API is running, now check for the model
        self.chat_display.append("🟢 Ollama API Connected. Checking for model...")
        QtCore.QCoreApplication.processEvents()

        if check_ollama_model_availability(self.model_name):
            self.layout_stack.setCurrentIndex(1) # Switch to chat view
            self.chat_display.append(f"🟢 Model '{self.model_name}' found. Ready.")
            
            # Get last update from brain file
            brain_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'ai_brain.py')
            if os.path.exists(brain_path):
                mtime = os.path.getmtime(brain_path)
                last_update = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                self.chat_display.append(f"<small style='color: #888;'>Last Update: {last_update}</small>")
            
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            self.layout_stack.setCurrentIndex(1) # Stay on chat view to show error
            self.chat_display.append(f"🔴 Model '{self.model_name}' not found.")
            self.chat_display.append(f"Please run <b><code>ollama pull {self.model_name}</code></b> in your terminal and restart QGIS.")
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
        """
        Manages the multi-step conversation with the AI agent.
        It sends the user prompt, handles tool calls from the AI,
        and displays the final response.
        """
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        self.user_input.setPlaceholderText("Agent is thinking...")
        self.user_input.setEnabled(False)
        self.send_button.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

        # Use persistent history, but clear it if user explicitly asks for a 'new' session
        if user_text.lower() in ["clear", "reset", "new chat"]:
            self.conversation_history = []
            self.chat_display.append("<br><i>History cleared.</i>")
            return

        # Initialize the turn-specific history
        current_turn_history = [{"role": "user", "content": user_text}]
        
        try:
            max_steps = 10  # Increased for more complex reasoning headroom
            for step in range(max_steps):
                QgsMessageLog.logMessage(f"AtQuery Agent: Step {step + 1}", "AtQuery", 0)

                # Send combined history (limit to last 5 full turns = ~10-15 messages)
                combined_history = self.conversation_history[-10:] + current_turn_history
                ai_response_message = self._get_ai_response(combined_history)
                current_turn_history.append(ai_response_message)

                # If there are no tool calls, it's the final answer
                if not ai_response_message.get("tool_calls"):
                    QgsMessageLog.logMessage("AtQuery Agent: Received final answer.", "AtQuery", 0)
                    self.handle_ai_response(ai_response_message.get("content", ""))
                    break

                # --- If we are here, the AI wants to call a tool ---
                QgsMessageLog.logMessage("AtQuery Agent: Handling tool calls.", "AtQuery", 0)
                tool_calls = ai_response_message["tool_calls"]
                
                # Execute all tool calls and gather results
                tool_outputs = []
                for tool_call in tool_calls:
                    tool_output_content = self.handle_tool_call(json.dumps(tool_call))
                    tool_outputs.append({
                        "role": "tool",
                        "content": tool_output_content,
                        "tool_call_id": tool_call.get("id") # Pass the ID back
                    })
                
                # Add all tool outputs to the message history
                current_turn_history.extend(tool_outputs)

            else: # This else belongs to the for loop
                self.handle_ai_response("The agent could not finish its task in the maximum number of steps.")

            # AT THE END: Persist the whole turn to the main history
            self.conversation_history.extend(current_turn_history)
            if len(self.conversation_history) > 30: # Hard limit
                self.conversation_history = self.conversation_history[-30:]

        except Exception as e:
            error_message = f"An error occurred: {str(e)}\n{traceback.format_exc()}"
            self.chat_display.append(f"<br><b>Error:</b> {str(e)}")
            QgsMessageLog.logMessage(error_message, "AtQuery", 2)

        finally:
            self.user_input.setPlaceholderText("Enter your PyQGIS request...")
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)
            self.user_input.setFocus()

    def _get_ai_response(self, messages):
        """
        Sends a list of messages to the Ollama API and returns the AI's response message.
        """
        # --- History Sanitization ---
        # The 3B model is prone to adding prefixes like "None," or "Answer:".
        # We strip these from the history so they don't pollute the context and cause loops.
        sanitized_messages = []
        prefixes_to_strip = [
            "AtQuery:", "User:", "Answer:", "Response:", "Thought:",
            "AtQuery Response:", "AI:", "Assistant:", "None,"
        ]
        
        for msg in messages:
            new_msg = msg.copy()
            if msg.get('role') == 'assistant' and msg.get('content'):
                content = msg['content'].strip()
                changed = True
                while changed:
                    changed = False
                    for prefix in prefixes_to_strip:
                        if content.lower().startswith(prefix.lower()):
                            content = content[len(prefix):].strip()
                            changed = True
                            break
                new_msg['content'] = content
            sanitized_messages.append(new_msg)

        # Ensure system prompt is the first message
        full_messages = [{"role": "system", "content": get_system_prompt()}] + sanitized_messages

        payload = {
            "model": self.model_name,
            "messages": full_messages,
            "tools": get_tools(),
            "stream": False,
            "options": {
                "stop": ["User:", "AtQuery:", "Response:", "Thought:", "\n\n"]
            }
        }
        
        QgsMessageLog.logMessage(f"AtQuery Debug: Ollama Request Payload: {json.dumps(payload, indent=2)}", "AtQuery", 0)
        
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post('http://localhost:11434/api/chat', headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            QgsMessageLog.logMessage(f"AtQuery Debug: Ollama Raw Response: {json.dumps(data, indent=2)}", "AtQuery", 0)
            
            msg = data['message']
            
            # Fallback: If 'tool_calls' is empty but 'content' looks like JSON, try to parse it
            if not msg.get('tool_calls') and msg.get('content'):
                content = msg['content'].strip()
                
                # Strip trailing quotes or messy closures
                while content.endswith('"') or content.endswith("'"):
                    content = content[:-1].strip()
                
                if '{' in content and ('function' in content or 'name' in content):
                    try:
                        # Extract JSON-like substring
                        start_idx = content.find('{')
                        end_idx = content.rfind('}') + 1
                        json_str = content[start_idx:end_idx]
                        
                        # Fix common key mismatches and string-vs-object failures
                        json_str = json_str.replace('"parameters"', '"arguments"')
                        
                        # Handle the common "function": "name" vs "function": {"name": "name"} failure
                        import re
                        # If "function": "string", change to "function": {"name": "string"}
                        json_str = re.sub(r'"function":\s*"([^"]+)"', r'"function": {"name": "\1"}', json_str)
                        
                        # DEFENSIVE: Handle unescaped nested double quotes in the "sql" field
                        # Example: "sql": "NAME = "Value"" -> "sql": "NAME = 'Value'"
                        # We use a non-greedy search for the value of the sql key
                        sql_matches = re.finditer(r'"sql":\s*"(.*?)"(?=[\s,}])', json_str)
                        for match in sql_matches:
                            full_sql_entry = match.group(0)
                            sql_content = match.group(1)
                            if '"' in sql_content:
                                fixed_sql_content = sql_content.replace('"', "'")
                                json_str = json_str.replace(full_sql_entry, f'"sql": "{fixed_sql_content}"')

                        extra_data = json.loads(json_str)
                        
                        # Uniform repair into tool_calls list
                        raw_calls = []
                        if isinstance(extra_data, dict):
                            if 'tool_calls' in extra_data:
                                raw_calls = extra_data['tool_calls']
                            elif 'function' in extra_data or 'name' in extra_data:
                                raw_calls = [extra_data]
                        elif isinstance(extra_data, list):
                            raw_calls = extra_data

                        # Final normalization to ensure Ollama accepts it back in history
                        normalized_calls = []
                        for call in raw_calls:
                            # 1. Handle "naked" function objects (e.g., {"name": "...", "arguments": {}})
                            if 'name' in call and 'function' not in call:
                                func_obj = call
                            else:
                                func_obj = call.get('function', {})
                                
                            # 2. Map parameters to arguments
                            if 'parameters' in func_obj and 'arguments' not in func_obj:
                                func_obj['arguments'] = func_obj.pop('parameters')
                            
                            # 3. DEFENSIVE: Replace common placeholders with last known valid names
                            args = func_obj.get('arguments', {})
                            for k, v in args.items():
                                if isinstance(v, str) and v.lower() in ["your_layer_name", "layer_name_here", "example_layer", "some_layer"]:
                                    # Fallback search for a layer name in history (messages)
                                    for prev in reversed(messages):
                                        if prev.get('role') == 'tool':
                                            try:
                                                tool_data = json.loads(prev['content'])
                                                # Look for 'layers' list in QgsProject_mapLayers output
                                                if 'layers' in tool_data and isinstance(tool_data['layers'], list) and tool_data['layers']:
                                                    args[k] = tool_data['layers'][0]
                                                    break
                                            except:
                                                pass
                                    
                            # 4. Re-structure into valid tool_call object
                            normalized_calls.append({
                                "id": call.get('id', f"call_{time.time_ns()}"),
                                "type": "function",
                                "function": {
                                    "name": str(func_obj.get('name', '')),
                                    "arguments": args
                                }
                            })
                        
                        if normalized_calls:
                            msg['tool_calls'] = normalized_calls
                            msg['content'] = content[:start_idx].strip()
                            
                    except Exception as parse_err:
                        QgsMessageLog.logMessage(f"AtQuery Warning: Detailed JSON repair failed: {str(parse_err)}", "AtQuery", 1)
            
            return msg
        except requests.exceptions.RequestException as e:
            error_details = ""
            if hasattr(response, 'text'):
                error_details = f" - Response: {response.text}"
            raise Exception(f"Ollama API Error: {str(e)}{error_details}")

    def _resolve_layer(self, layer_name):
        """
        Attempts to find a QGIS layer by name using multiple strategies:
        1. Exact match.
        2. Case-insensitive match.
        3. Stripping common suffixes added by models (e.g. " - DCD").
        4. Matching by stem (e.g. "AdminArea" matches "AdminArea_DCD...").
        """
        if not layer_name: return None
        
        project = QgsProject.instance()
        
        # 1. Exact Match
        matches = project.mapLayersByName(layer_name)
        if matches: return matches[0]
        
        # 2. Iterative Search through all layers
        all_layers = project.mapLayers().values()
        
        # Strategy A: Case-insensitive match
        for l in all_layers:
            if str(l.name()).lower() == layer_name.lower():
                return l
                
        # Strategy B: Suffix Stripping (Handle hallucinations like "Name - DCD")
        if " - " in layer_name:
            base_name = layer_name.split(" - ")[0].strip()
            for l in all_layers:
                if str(l.name()).lower() == base_name.lower():
                    return l

        # Strategy C: Stem matching (If the requested name is a substring of the layer name)
        # This is useful when the model truncates very long names.
        for l in all_layers:
            if layer_name.lower() in str(l.name()).lower() or str(l.name()).lower() in layer_name.lower():
                return l
                
        return None

    def handle_tool_call(self, tool_call_json):
        """
        Executes a single tool call from the AI and returns its output as a JSON string.
        This function is designed to be robust against malformed inputs from the LLM
        and to prevent serialization errors during testing with mock objects.
        """
        try:
            tool_call = json.loads(tool_call_json)
            func_info = tool_call.get("function", {})
            name = func_info.get("name")
            # Arguments can be a JSON string (OpenAI style) or a dict (Ollama style)
            args_raw = func_info.get("arguments", {})
            args = {}
            
            if isinstance(args_raw, dict):
                args = args_raw
            elif isinstance(args_raw, str) and args_raw.strip():
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError:
                    return json.dumps({"error": f"Tool '{name}' was called with malformed JSON arguments: {args_raw}"})
            
            QgsMessageLog.logMessage(f"Executing tool: {name} with args: {args}", "AtQuery", 0)

            # --- Tool Dispatch ---
            if name == 'QgsProject_mapLayers':
                layers = QgsProject.instance().mapLayers().values()
                layer_names = [str(l.name()) for l in layers]
                return json.dumps({"layers": layer_names})

            elif name == 'QgsVectorLayer_fields':
                layer_name = args.get('layer_name')
                if not layer_name:
                    return json.dumps({"error": "Missing required argument: 'layer_name'"})
                
                layer = self._resolve_layer(layer_name)
                if not layer:
                    return json.dumps({"error": f"Layer '{layer_name}' not found."})
                
                fields = [str(field.name()) for field in layer.fields()]
                return json.dumps({"layer_name": str(layer.name()), "fields": fields})

            elif name == 'QgsVectorLayer_selectByExpression':
                layer_name = args.get('layer_name')
                sql = args.get('sql')

                if not layer_name or not sql:
                    return json.dumps({"error": "Missing required arguments: 'layer_name' and 'sql'"})

                layer = self._resolve_layer(layer_name)
                if not layer:
                    return json.dumps({"error": f"Layer '{layer_name}' not found."})

                if not isinstance(layer, QgsVectorLayer):
                    return json.dumps({"error": f"Layer '{layer.name()}' is not a vector layer."})

                layer.selectByExpression(sql)
                count = layer.selectedFeatureCount()
                
                if count > 0:
                    self.iface.mapCanvas().zoomToSelected(layer)
                
                return json.dumps({
                    "layer": str(layer.name()),
                    "sql": str(sql),
                    "count": int(count),
                    "action": "Selected and zoomed to"
                })
            
            elif name == 'processing_run_joinattributestable':
                input_layer_name = args.get('input_layer_name')
                join_layer_name = args.get('join_layer_name')
                input_join_field = args.get('input_join_field')
                join_layer_field = args.get('join_layer_field')
                join_prefix = args.get('join_prefix', '')

                if not all([input_layer_name, join_layer_name, input_join_field, join_layer_field]):
                    return json.dumps({"error": "Missing one or more required arguments for join."})

                input_layer = self._resolve_layer(input_layer_name)
                join_layer = self._resolve_layer(join_layer_name)

                if not input_layer:
                    return json.dumps({"error": f"Input layer '{input_layer_name}' not found."})
                if not join_layer:
                    return json.dumps({"error": f"Join layer '{join_layer_name}' not found."})

                alg_params = {
                    'INPUT': input_layer,
                    'FIELD': input_join_field,
                    'INPUT_2': join_layer,
                    'FIELD_2': join_layer_field,
                    'PREFIX': join_prefix,
                    'OUTPUT': 'memory:'
                }

                try:
                    result = processing.run("qgis:joinattributestable", alg_params)
                    QgsProject.instance().addMapLayer(result['OUTPUT'])
                    
                    return json.dumps({
                        "status": "success",
                        "message": f"Join completed. Fields from '{str(join_layer_name)}' added to '{str(input_layer_name)}'."
                    })
                except Exception as e:
                    return json.dumps({"error": f"Join algorithm failed: {str(e)}"})

            elif name == 'processing_run_native_buffer':
                layer_name = args.get('layer_name')
                distance = args.get('distance')
                output_layer_name = args.get('output_layer_name')
                
                if not layer_name or distance is None:
                    return json.dumps({"error": "Missing required arguments: 'layer_name' and 'distance'"})
                
                layer = self._resolve_layer(layer_name)
                if not layer:
                    return json.dumps({"error": f"Layer '{layer_name}' not found."})
                
                if not isinstance(layer, QgsVectorLayer):
                    return json.dumps({"error": f"Layer '{layer_name}' is not a vector layer."})
                
                if not output_layer_name:
                    output_layer_name = f"{layer_name}_buffer_{distance}m"
                
                alg_params = {
                    'INPUT': layer,
                    'DISTANCE': distance,
                    'SEGMENTS': 5,
                    'END_CAP_STYLE': 0,
                    'JOIN_STYLE': 0,
                    'MITER_LIMIT': 2,
                    'DISSOLVE': False,
                    'OUTPUT': 'memory:'
                }
                
                try:
                    result = processing.run("native:buffer", alg_params)
                    output_layer = result['OUTPUT']
                    output_layer.setName(output_layer_name)
                    QgsProject.instance().addMapLayer(output_layer)
                    
                    return json.dumps({
                        "status": "success",
                        "layer_name": str(output_layer_name),
                        "message": f"Buffer layer '{str(output_layer_name)}' created successfully with {distance}m distance."
                    })
                except Exception as e:
                    return json.dumps({"error": f"Buffer algorithm failed: {str(e)}"})

            elif name == 'QgsVectorLayer_createMemoryLayer':
                layer_name = args.get('layer_name', 'BoundingBox')
                extent_str = args.get('extent', '@map_extent')
                
                if extent_str == '@map_extent':
                    extent = self.iface.mapCanvas().extent()
                else:
                    try:
                        coords = [float(x.strip()) for x in extent_str.split(',')]
                        extent = QgsRectangle(coords[0], coords[1], coords[2], coords[3])
                    except (ValueError, IndexError):
                        return json.dumps({"error": "Invalid extent format. Use 'xmin,ymin,xmax,ymax'."})
                
                crs = self.iface.mapCanvas().mapSettings().destinationCrs().authid()
                new_layer = QgsVectorLayer(f"Polygon?crs={crs}", layer_name, "memory")
                
                if not new_layer.isValid():
                    return json.dumps({"error": "Failed to create memory layer."})
                
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromRect(extent))
                new_layer.dataProvider().addFeatures([feature])
                new_layer.updateExtents()
                QgsProject.instance().addMapLayer(new_layer)
                
            elif name == 'QgsApplication_processingRegistry_algorithms':
                search_term = args.get('search_term', '').lower()
                from qgis.core import QgsApplication
                
                results = []
                for alg in QgsApplication.processingRegistry().algorithms():
                    if search_term in alg.name().lower() or search_term in alg.displayName().lower():
                        results.append({
                            "id": str(alg.id()),
                            "name": str(alg.name()),
                            "displayName": str(alg.displayName())
                        })
                        # Limit results to 20 to avoid context overflow
                        if len(results) >= 20:
                            break
                
                return json.dumps({"algorithms": results})

            elif name == 'processing_algorithmHelp':
                algorithm_id = args.get('algorithm_id')
                if not algorithm_id:
                    return json.dumps({"error": "Missing required argument: 'algorithm_id'"})
                
                # We need to capture the output of processing.algorithmHelp
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    processing.algorithmHelp(algorithm_id)
                help_text = f.getvalue()
                
                if not help_text.strip():
                    return json.dumps({"error": f"No help found for algorithm '{algorithm_id}'."})
                
                return json.dumps({"algorithm_id": str(algorithm_id), "help": help_text})

            elif name == 'processing_run':
                algorithm_id = args.get('algorithm_id')
                params = args.get('parameters', {})
                
                if not algorithm_id:
                    return json.dumps({"error": "Missing required argument: 'algorithm_id'"})

                # Handle layer names in parameters - convert string names to layer objects
                processed_params = {}
                for key, value in params.items():
                    if isinstance(value, str) and value not in ['memory:', 'TEMPORARY_OUTPUT']:
                        # Check if it's a layer name
                        layer_list = QgsProject.instance().mapLayersByName(value)
                        if layer_list:
                            processed_params[key] = layer_list[0]
                        else:
                            processed_params[key] = value
                    else:
                        processed_params[key] = value

                try:
                    result = processing.run(algorithm_id, processed_params)
                    
                    # If there's an OUTPUT or similar key in the result, add it to the project if it's a layer
                    for key, output_value in result.items():
                        if isinstance(output_value, (QgsVectorLayer, QgsMapLayer)):
                            QgsProject.instance().addMapLayer(output_value)
                        elif isinstance(output_value, str) and os.path.exists(output_value):
                            # Try to load it if it's a file path result
                            new_layer = QgsVectorLayer(output_value, f"Output_{key}", "ogr")
                            if new_layer.isValid():
                                QgsProject.instance().addMapLayer(new_layer)

                    return json.dumps({
                        "status": "success",
                        "algorithm_id": str(algorithm_id),
                        "results": {k: str(v) for k, v in result.items()},
                        "message": f"Algorithm '{algorithm_id}' executed successfully."
                    })
                except Exception as e:
                    return json.dumps({"error": f"Processing algorithm failed: {str(e)}"})

            else:
                return json.dumps({"error": f"Tool '{name}' not found."})

        except Exception as e:
            error_info = f"Tool execution failed: {traceback.format_exc()}"
            QgsMessageLog.logMessage(error_info, "AtQuery", 2)
            return json.dumps({"error": str(e)})

    def check_ollama_model_availability(self):
        """Check if the specified Ollama model is available."""
        try:
            response = requests.get('http://localhost:11434/api/tags')
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model_name in model_names:
                    QgsMessageLog.logMessage(f"Model '{self.model_name}' is available.", "AtQuery", 0)
                    return True
                else:
                    # Provide helpful guidance for common issues
                    if "llama3:latest" in model_names and "llama3.1" not in str(model_names):
                        error_msg = (
                            f"Model '{self.model_name}' not found. You have 'llama3:latest' which does NOT support function calling.\n"
                            f"Please install llama3.1 using: ollama pull llama3.1"
                        )
                    else:
                        error_msg = (
                            f"Model '{self.model_name}' not found. Available models: {', '.join(model_names)}.\n"
                            f"Install it using: ollama pull {self.model_name}"
                        )
                    
                    QgsMessageLog.logMessage(error_msg, "AtQuery", 2)
                    self.chat_display.append(f"<b>Error:</b> {error_msg}")
                    return False
            else:
                return False
        except requests.exceptions.RequestException:
            return False

    def handle_ai_response(self, response_text):
        """Displays the final AI answer."""
        if not response_text.strip():
            response_text = "The agent finished its work without a final message."
        
        # --- UI Sanity Filter: Strip roleplay prefixes ---
        prefixes_to_strip = [
            "AtQuery:", "User:", "Answer:", "Response:", "Thought:",
            "AtQuery Response:", "AI:", "Assistant:", "None,"
        ]
        
        cleaned_text = response_text.strip()
        
        # Iteratively strip prefixes (in case there are multiple)
        changed = True
        while changed:
            changed = False
            for prefix in prefixes_to_strip:
                if cleaned_text.lower().startswith(prefix.lower()):
                    cleaned_text = cleaned_text[len(prefix):].strip()
                    changed = True
                    break
        
        if not cleaned_text:
            cleaned_text = "The agent finished its work without a final message."

        self.chat_display.append(f"<br><b>AtQuery:</b> {cleaned_text}")

    def closeEvent(self, event):
        """Handles the close event to emit a signal."""
        self.closingPlugin.emit()
        super().closeEvent(event)