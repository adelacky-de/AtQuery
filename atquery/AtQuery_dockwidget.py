#AtQuery_dockwidget.oy

import requests
import json
import traceback
import os
import tempfile
import ast
import re

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import QEvent

# Core QGIS imports — only what we actually use
from qgis.core import (
    QgsProject,
    QgsMessageLog,
    QgsFeatureRequest,
    Qgis,
    QgsExpression
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
        # Start the conversation with the system prompt
        self.conversation_history = [{"role": "system", "content": get_system_prompt()}]
        
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
        """Adds user query to history and starts the AI conversation loop."""
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        self.user_input.setPlaceholderText("Thinking...")
        self.user_input.setEnabled(False)
        self.send_button.setEnabled(False)
        QtCore.QCoreApplication.processEvents()

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_text})
        
        # Start the conversation loop
        self._run_ai_conversation()

    def _run_ai_conversation(self):
        """
        Manages the multi-step conversation with the AI.
        It sends the history, gets a response, executes tools, and continues
        until the AI provides a final answer for the user.
        """
        try:
            while True:
                # Get AI response based on the current conversation history
                ai_message, tool_calls = self._get_ai_response(self.conversation_history)

                # If the AI calls a tool, execute it (even if it also returned text).
                if tool_calls:
                    QgsMessageLog.logMessage(f"Executing {len(tool_calls)} tool call(s)", "AtQuery", Qgis.Info)
                    if ai_message:
                        self.chat_display.append(f"<br><b>AtQuery (thinking):</b> {ai_message}")
                        self.conversation_history.append({"role": "assistant", "content": ai_message})

                    # Record the serialized tool call for context
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": json.dumps(tool_calls)
                    })
                    
                    for tool_call in tool_calls:
                        QgsMessageLog.logMessage(f"Tool call: {tool_call.get('function', {}).get('name', 'unknown')}", "AtQuery", Qgis.Info)
                        result_data = self.handle_tool_call(tool_call)
                        QgsMessageLog.logMessage(f"Tool result: {json.dumps(result_data)}", "AtQuery", Qgis.Info)
                        self._display_tool_result(result_data) 
                        self.conversation_history.append({
                            "role": "tool",
                            "content": json.dumps(result_data)
                        })
                        if tool_call['function']['name'] in ('get_layer_list', 'get_layer_fields'):
                            return

                    # After executing tools, continue the loop to let the AI respond with the final message
                    continue

                # If no tool call, any AI message is the final response.
                if ai_message:
                    self.chat_display.append(f"<br><b>AtQuery:</b> {ai_message}")
                    self.conversation_history.append({"role": "assistant", "content": ai_message})
                    break # End of conversation turn

                else:
                    # If the AI returns neither a message nor a tool call, it's an unexpected state.
                    self.chat_display.append("<br><b>AtQuery:</b> I'm not sure how to proceed. Please try again.")
                    break

        except Exception as e:
            error_message = f"AtQuery Error: {traceback.format_exc()}"
            self.chat_display.append(f"<br>Error: Could not reach Ollama. Is it running?")
            QgsMessageLog.logMessage(error_message, "AtQuery", Qgis.Critical)

        finally:
            # Re-enable user input
            self.user_input.setPlaceholderText("Ask anything about your project...")
            self.user_input.setEnabled(True)
            self.send_button.setEnabled(True)

    def handle_tool_call(self, tool_call):
        """Executes a single tool call and returns a structured dictionary."""
        try:
            name = tool_call['function']['name']
            args = tool_call['function'].get('arguments', {})

            if name == 'get_layer_list':
                layers = QgsProject.instance().mapLayers().values()
                return {"action": "get_layer_list", "layers": [l.name() for l in layers]}

            elif name == 'get_layer_fields':
                layer_name = args.get('layer_name')
                layer = next((l for l in QgsProject.instance().mapLayers().values() if l.name() == layer_name), None)
                if not layer:
                    return {"error": f"Layer '{layer_name}' not found."}
                
                fields = [field.name() for field in layer.fields()]
                return {"action": "get_layer_fields", "layer": layer_name, "fields": fields}

            elif name in ('query_layer', 'select_features'):
                layer_name = args.get('layer_name')
                raw_sql = args.get('sql')
                QgsMessageLog.logMessage(
                    f"AI tool call '{name}' with raw args: {args}",
                    "AtQuery",
                    Qgis.Info
                )
                sql = self._sanitize_sql(raw_sql)

                if not layer_name or not sql:
                    return {"error": "Both 'layer_name' and 'sql' are required for this tool."}

                layer = next((l for l in QgsProject.instance().mapLayers().values() if l.name() == layer_name), None)
                if not layer:
                    return {"error": f"Layer '{layer_name}' not found."}

                expr = QgsExpression(sql)
                if expr.hasParserError():
                    return {
                        "error": f"Invalid query syntax: {expr.parserErrorString()}",
                        "sql": sql
                    }

                # Count matching features safely (featureCount does not accept requests directly)
                if sql:
                    request = QgsFeatureRequest(expr)
                    count = sum(1 for _ in layer.getFeatures(request))
                else:
                    count = layer.featureCount()


                action_verb = "Found"
                if name == 'select_features':
                    layer.selectByExpression(sql)
                    if count > 0:
                        self.iface.mapCanvas().zoomToSelected(layer)
                    action_verb = "Selected"

                return {
                    "action": name,
                    "layer": layer_name,
                    "sql": sql,
                    "count": count,
                    "action_verb": action_verb
                }
            
            return {"error": f"Unknown tool: {name}"}

        except Exception as e:
            return {"error": str(e)}

    def _display_tool_result(self, result_data):
        """Formats and displays the result of a tool call to the user."""
        if "error" in result_data:
            message = f"An error occurred: {result_data['error']}"
        elif result_data.get("action") == "get_layer_list":
            layers = result_data.get('layers', [])
            if layers:
                layer_list = "<br>- ".join(layers)
                message = f"Available layers:<br>- {layer_list}"
            else:
                message = "No layers found in the project."
        elif result_data.get("action") == "get_layer_fields":
            fields = result_data.get('fields', [])
            layer_name = result_data.get('layer', 'the layer')
            if fields:
                field_list = "<br>- ".join(fields)
                message = f"Fields in '{layer_name}':<br>- {field_list}"
            else:
                message = f"No fields found in '{layer_name}'."
        elif result_data.get("action") in ("query_layer", "select_features"):
            count = result_data.get('count', 0)
            layer = result_data.get('layer', 'the layer')
            action_verb = result_data.get('action_verb', 'Processed')
            feature_word = "feature" if count == 1 else "features"
            message = f"✅ {action_verb} {count} {feature_word} in '{layer}'."
        else:
            # Generic message for unhandled tool outputs
            message = f"Completed: {result_data.get('action', 'unspecified action')}."

        self.chat_display.append(f"<br><b>AtQuery:</b> {message}")

    def _sanitize_sql(self, sql_value):
        """
        Attempts to convert imperfect SQL strings (e.g., ["FIELD", "value"]) into valid expressions.
        Returns a cleaned string or an empty string if nothing useful could be derived.
        """
        sql = (sql_value or "").strip()
        if not sql:
            return ""

        # First, unescape any escaped quotes (handle \' and \")
        sql = sql.replace("\\'", "'").replace('\\"', '"')

        # Normalize fancy unicode quotes into standard ASCII equivalents
        # Using replace() instead of translate() to avoid encoding issues
        sql = sql.replace(""", '"').replace(""", '"')
        sql = sql.replace("„", '"').replace("‟", '"')
        sql = sql.replace("'", "'").replace("'", "'").replace("‛", "'")

        # Check if SQL is already in correct format (field in double quotes, value in single quotes)
        if self._is_already_valid_sql(sql):
            return sql

        # Collapse doubled double-quotes that come from JSON escaping (""FIELD"")
        sql = self._collapse_double_quotes(sql)
        
        # Try to normalize basic equals expressions
        normalized = self._normalize_basic_equals(sql)
        if normalized:
            return normalized

        # Try parsing as Python literal (list/tuple)
        literal_candidate = self._try_literal_sql(sql)
        if literal_candidate:
            return literal_candidate

        # Try inferring missing operator
        inferred = self._infer_missing_operator(sql)
        if inferred:
            return inferred

        # If all else fails, return the original (might already be valid)
        return sql

    def _try_literal_sql(self, sql):
        """Parses python-style literals like ["FIELD", "value"] into `"FIELD" = 'value'`."""
        if not sql.startswith(("[", "(")):
            return ""

        try:
            literal = ast.literal_eval(sql)
        except Exception:
            return ""

        if isinstance(literal, (list, tuple)):
            if len(literal) == 2:
                field, value = literal
                operator = "="
            elif len(literal) == 3:
                field, operator, value = literal
                operator = operator or "="
            else:
                return ""

            if not isinstance(field, str):
                return ""

            field_expr = field if field.startswith('"') and field.endswith('"') else f"\"{field}\""

            if isinstance(value, str):
                clean_value = value.strip()
                if clean_value.startswith("'") and clean_value.endswith("'"):
                    clean_value = clean_value[1:-1]
                clean_value = clean_value.replace("'", "''")
                value_expr = f"'{clean_value}'"
            else:
                value_expr = str(value)

            op = str(operator).strip() or "="
            return f"{field_expr} {op} {value_expr}"

        return ""

    def _infer_missing_operator(self, sql):
        """
        Handles cases like `"NAME_EN" 'Southern District'` by inserting '=' between field and value.
        """
        if '"' in sql and "'" in sql and "=" not in sql:
            try:
                field_part, rest = sql.split('"', 2)[1:]
                value_part = rest.split("'", 2)[1]
                return f"\"{field_part}\" = '{value_part}'"
            except ValueError:
                return ""
        return ""

    def _is_already_valid_sql(self, sql):
        """
        Checks if SQL is already in valid QGIS format: "FIELD" = 'value' or similar.
        Returns True if it looks valid, False otherwise.
        """
        # Quick check: if it has a field in double quotes and a value in single quotes, it's likely valid
        if '"' in sql and "'" in sql and "=" in sql:
            # Try to parse it as a QgsExpression to see if it's valid
            try:
                expr = QgsExpression(sql)
                if not expr.hasParserError():
                    return True
            except Exception:
                pass
        return False

    def _collapse_double_quotes(self, sql):
        """Reduces runs of repeated double quotes to a single double quote."""
        return re.sub(r'"{2,}', '"', sql)

    def _normalize_basic_equals(self, sql):
        """
        For simple expressions that only contain '=', ensures fields use double quotes
        and string literals use single quotes.
        Returns None if normalization fails (so caller can try other methods).
        """
        if "=" not in sql:
            return None

        try:
            left, right = sql.split("=", 1)
            normalized_field = self._normalize_field_name(left)
            normalized_value = self._normalize_value_literal(right)

            if not normalized_field or not normalized_value:
                return None

            return f"{normalized_field} = {normalized_value}"
        except Exception:
            return None

    def _normalize_field_name(self, raw_field):
        field = raw_field.strip()
        while len(field) >= 2 and field[0] in ("'", '"') and field[-1] == field[0]:
            field = field[1:-1].strip()

        if not field:
            return ""

        return f"\"{field}\""

    def _normalize_value_literal(self, raw_value):
        value = raw_value.strip()
        if not value:
            return ""

        # Remove outer quotes (both single and double) iteratively
        while len(value) >= 2:
            if value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1].strip()
            else:
                break

        if not value:
            return ""

        # If the value is numeric, keep as-is
        try:
            float(value)
            return value
        except ValueError:
            pass

        # Escape single quotes by doubling them (QGIS SQL standard)
        clean_value = value.replace("'", "''")
        return f"'{clean_value}'"
    
    def _try_parse_tool_call_from_text(self, text):
        """
        Attempts to extract a tool call from text that looks like JSON.
        Returns a tool_call dict if found, None otherwise.
        """
        text = text.strip()
        
        # Try to find JSON object in the text - handle nested objects
        import re
        # First, try to parse the entire text as JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "name" in parsed and "parameters" in parsed:
                return {
                    "function": {
                        "name": parsed["name"],
                        "arguments": parsed["parameters"]
                    }
                }
        except json.JSONDecodeError:
            pass
        
        # If that fails, try to extract JSON from within the text
        # Look for pattern: {"name": "...", "parameters": {...}}
        # Use a more robust approach: find the opening brace and try to parse balanced braces
        brace_start = text.find('{')
        if brace_start >= 0:
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i in range(brace_start, len(text)):
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found balanced braces
                            json_str = text[brace_start:i+1]
                            try:
                                parsed = json.loads(json_str)
                                if isinstance(parsed, dict) and "name" in parsed and "parameters" in parsed:
                                    return {
                                        "function": {
                                            "name": parsed["name"],
                                            "arguments": parsed["parameters"]
                                        }
                                    }
                            except json.JSONDecodeError as e:
                                QgsMessageLog.logMessage(f"JSON parse error: {str(e)} for: {json_str[:100]}", "AtQuery", Qgis.Warning)
                            break
        
        return None
        
    def _get_ai_response(self, messages):
        """
        Sends the conversation history to the local Ollama server.
        Returns (ai_message_for_user, list_of_tool_calls).
        """
        model = "llama3.2:3b-instruct-q4_K_M" 
        
        payload = {
            "model": model,
            "messages": messages,
            "tools": get_tools(),
            "stream": False
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://localhost:11434/api/chat', headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        ai_response_message = data.get('message', {})
        
        # Extract text content and tool calls from the AI's response
        ai_message_for_user = ai_response_message.get('content', '')
        tool_calls = ai_response_message.get('tool_calls', [])
        
        # Fallback: If no tool_calls but the message contains JSON that looks like a tool call, parse it
        if not tool_calls and ai_message_for_user:
            parsed_tool_call = self._try_parse_tool_call_from_text(ai_message_for_user)
            if parsed_tool_call:
                QgsMessageLog.logMessage(f"Extracted tool call from text: {json.dumps(parsed_tool_call)}", "AtQuery", Qgis.Info)
                tool_calls = [parsed_tool_call]
                ai_message_for_user = ""  # Clear the message since we're using the tool call
            else:
                QgsMessageLog.logMessage(f"Failed to parse tool call from text: {ai_message_for_user[:200]}", "AtQuery", Qgis.Warning)
        
        return ai_message_for_user, tool_calls