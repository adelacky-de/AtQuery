import requests
import sys
import os
import subprocess
from qgis.core import QgsMessageLog

def check_ollama_api():
    """Checks if the Ollama API server is running on the default port."""
    try:
        requests.get('http://localhost:11434', timeout=1)
        return True
    except requests.exceptions.RequestException:
        return False

def check_ollama_model_availability(model_name: str) -> bool:
    """Checks if a specific model is available in the Ollama service."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        models = data.get("models", [])
        for model in models:
            if model.get("name") == model_name:
                QgsMessageLog.logMessage(f"Found required model: {model_name}", "AtQuery", 0)
                return True
        
        QgsMessageLog.logMessage(f"Model '{model_name}' not found in Ollama.", "AtQuery", 1)
        return False
    except requests.exceptions.RequestException as e:
        QgsMessageLog.logMessage(f"Could not connect to Ollama to check for models: {e}", "AtQuery", 2)
        return False

def get_os_info():
    """Identifies the operating system for installer selection."""
    platform = sys.platform.lower()
    if platform.startswith('darwin'):
        return 'mac'
    elif platform.startswith('win'):
        return 'win'
    else:
        return 'other'
    
def get_installer_url(os_type):
    """Gets the download URL for the Ollama installer based on OS."""
    if os_type == 'mac': 
        return 'https://ollama.com/download/Ollama-darwin.zip'
    elif os_type == 'win': 
        return 'https://ollama.com/download/OllamaSetup.exe'
    else: 
        return None

def download_installer(url, output_path, progress_callback):
    """
    Streams the download of the installer and updates the UI.
    Returns True on success, False on failure.
    """
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0:
            return False 

        chunk_size = 1024 * 1024  # 1 MB
        downloaded_size = 0

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    break
                f.write(chunk)
                downloaded_size += len(chunk)
                percent = int((downloaded_size / total_size) * 100)
                progress_callback(percent)
        return True
    except requests.exceptions.RequestException as e:
        QgsMessageLog.logMessage(f"Download failed: {e}", "AtQuery", 2)
        return False
    except IOError as e:
        QgsMessageLog.logMessage(f"File writing failed: {e}", "AtQuery", 2)
        return False

def launch_installer(file_path):
    """Launches the downloaded installer file."""
    os_type = get_os_info()
    try:
        if os_type == 'mac':
            subprocess.Popen(['open', os.path.dirname(file_path)])
            return True
        elif os_type == 'win':
            subprocess.Popen([file_path])
            return True
    except Exception as e:
        QgsMessageLog.logMessage(f"Failed to launch installer: {e}", "AtQuery", 2)
        return False
    return False
