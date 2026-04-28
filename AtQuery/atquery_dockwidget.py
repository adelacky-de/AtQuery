import requests
import json
import traceback
import sys
import os
import tempfile
from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.core import QgsProject, QgsApplication, QgsMessageLog
from qgis.PyQt.QtCore import QEvent
from .installer_utils import check_ollama_api, get_os_info, get_installer_url, download_installer, launch_installer
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
        """Processes the user's query."""
        user_text = self.user_input.text().strip()
        if not user_text:
            return

        self.chat_display.append(f"<br><b>You:</b> {user_text}")
        self.user_input.clear()
        self.user_input.setPlaceholderText("Waiting for AI response...")
        self.user_input.setEnabled(False)
        self.send_button.setEnabled(False)
        
        QtCore.QCoreApplication.processEvents() # Ensure UI updates

        # In a real QGIS plugin, this AI call would be moved to a QThread 
        # to prevent freezing the QGIS GUI. For simplicity here, we run it directly.
        try:
            response_text, tool_call_json = self._get_ai_response(user_text)
            
            if tool_call_json:
                # Handle Tool Call (e.g., getting layer list)
                tool_output = self.handle_tool_call(tool_call_json)
                
                # Send tool output back to the model for final answer generation (or display immediately)
                # For simplicity, we only display the layer list for now.
                self.chat_display.append(f"⚙️ [TOOL CALL: get_layer_list] Found layers: {tool_output}")
                
                # --- SECOND AI CALL WITH TOOL OUTPUT (REAL LLM pattern) ---
                # In a full implementation, you'd send a second request:
                # response_text, tool_call_json = self._get_ai_response(user_text, tool_output)
                
                # Since we often get code after the tool call, let's assume the first
                # response already contains the final code or answer.
                self.handle_ai_response(response_text)
                
            else:
                # Handle final code or text response
                self.handle_ai_response(response_text)

        except Exception as e:
            self.chat_display.append(f"<br>❌ An error occurred contacting Ollama: {str(e)}. Check your connection.")
            QgsMessageLog.logMessage(f"Ollama Contact Error: {traceback.format_exc()}", 'AtQuery', QgsMessageLog.CRITICAL)

        self.user_input.setPlaceholderText("Enter your PyQGIS request...")
        self.user_input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.check_ollama_status() # Re-check status just in case Ollama died

    def handle_tool_call(self, tool_call_json):
        """Executes the QGIS function requested by the AI."""
        if self.iface is None:
            QgsMessageLog.logMessage("iface is not set!", 'AtQuery', QgsMessageLog.CRITICAL)
            return "Error: QGIS interface not initialized."

        try:
            call = json.loads(tool_call_json)
            tool_name = call['function']['name']
            
            if tool_name == 'get_layer_list':
                # Implement the actual QGIS function
                layer_map = QgsProject.instance().mapLayers()
                layer_names = [layer.name() for layer in layer_map.values()]
                return ", ".join(layer_names)
                
            # Add other tools here as needed (e.g., get_layer_fields, get_selected_features)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Tool Call Error: {traceback.format_exc()}", 'AtQuery', QgsMessageLog.WARNING)
            return f"Error executing tool {tool_name}: {str(e)}"
            
    def _get_ai_response(self, prompt, tool_output=None):
        """
        Sends the request to the local Ollama server.
        Returns (response_text, tool_call_json).
        """
        model = "codellama" # Assuming this model is downloaded
        
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
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://localhost:11434/api/chat', headers=headers, json=payload)
        response.raise_for_status() # Raises an exception for bad status codes
        
        data = response.json()
        
        # Check for tool call
        if 'tool_calls' in data['message']:
            # Ollama returns a list of tool calls. We only support one for now.
            tool_call = data['message']['tool_calls'][0]
            tool_call_json = json.dumps(tool_call)
            return data['message']['content'] if 'content' in data['message'] else "", tool_call_json
        
        # Standard text/code response
        return data['message']['content'], None

    def handle_ai_response(self, response_text):
        """Determines if the AI returned code or text and processes it."""
        
        # Simple check to see if the response looks like code wrapped in markdown
        if "```python" in response_text or response_text.strip().startswith('iface.'):
            # It's code, so we try to execute it
            self.execute_code(response_text)
        else:
            # It's plain text, display it as an answer
            self.chat_display.append(f"<br><b>AtQuery:</b> {response_text}")

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
            execution_scope = {
                'iface': self.iface,
                'QgsProject': QgsProject,
                'QgsMessageLog': QgsMessageLog,
                # Redirect print() function output to the chat display
                'print': lambda x: self.chat_display.append(f"[OUTPUT] {x}")
            }
            
            exec(clean_code, execution_scope)
            
            self.chat_display.append("\n✅ [SUCCESS: Command Executed]")
            
        except Exception as e:
            self.chat_display.append(f"\n❌ [EXECUTION ERROR] {type(e).__name__}: {str(e)}")
            QgsMessageLog.logMessage(f"PyQGIS Execution Error: {traceback.format_exc()}", 'AtQuery', QgsMessageLog.CRITICAL)

    def closeEvent(self, event):
        """Handles the close event to emit a signal."""
        self.closingPlugin.emit()
        super().closeEvent(event)