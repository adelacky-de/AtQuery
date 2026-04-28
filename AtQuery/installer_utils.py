import requests
import sys
import os
import subprocess # NEW IMPORT NEEDED HERE

# Note: Ensure 'requests' and 'subprocess' are available in the QGIS Python environment.

def check_ollama_api():
    """Checks if the Ollama API server is running on the default port."""
    try:
        # Pings the base URL. If it's running, it will return a 200 status code.
        requests.get('http://localhost:11434', timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        # This exception is raised if the server is offline or connection is refused.
        return False
    except Exception:
        # Catch any other unexpected error 
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
    if os_type == 'mac': 
        # Ollama provides a zip on Mac
        return 'https://ollama.com/download/Ollama-darwin.zip'
    elif os_type == 'win': 
        return 'https://ollama.com/download/OllamaSetup.exe'
    else: 
        return None

def download_installer(url, output_path, progress_callback):
    """
    Streams the download of the installer, writes it to output_path,
    and updates the UI via progress_callback(percent).
    
    Returns True on success, False on failure.
    """
    try:
        # 1. Start the streaming request
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        # 2. Get the total file size from the header
        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0:
            return False 

        chunk_size = 1024 * 1024  # 1 MB chunks
        downloaded_size = 0

        # 3. Stream the content and write to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    break
                    
                f.write(chunk)
                downloaded_size += len(chunk)
                
                # 4. Calculate and update progress
                percent = int((downloaded_size / total_size) * 100)
                progress_callback(percent)
                
        return True

    except requests.exceptions.RequestException as e:
        print(f"Download failed: {e}") 
        return False
    except IOError as e:
        print(f"File writing failed: {e}")
        return False

def launch_installer(file_path):
    """Launches the downloaded installer file using subprocess."""
    os_type = get_os_info()
    
    if os_type == 'mac':
        # On Mac, we use 'open' to launch the folder containing the downloaded ZIP.
        # The user must manually unzip and drag the app to Applications.
        try:
            # os.path.dirname gets the folder where the file is saved
            subprocess.Popen(['open', os.path.dirname(file_path)])
            return True
        except Exception:
            return False
            
    elif os_type == 'win':
        # On Windows, executing the .exe starts the installer
        try:
            subprocess.Popen([file_path])
            return True
        except Exception:
            return False
            
    return False

# --- NEW FUNCTION TO ADD BELOW ---
def pull_codellama_model():
    """
    Executes the 'ollama pull codellama' command via the terminal.
    This function blocks the thread until the model is downloaded.
    Returns True on success, False on command failure.
    """
    try:
        command = ['ollama', 'pull', 'codellama']
        
        # subprocess.run executes the command, waits for completion, and checks 
        # the return code (due to check=True). If the return code is non-zero,
        # it raises a CalledProcessError.
        subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True
    
    except subprocess.CalledProcessError as e:
        # This occurs if the 'ollama pull' command itself fails (e.g., server error)
        print(f"Error executing 'ollama pull codellama': {e}")
        return False
        
    except FileNotFoundError:
        # This occurs if the 'ollama' command is not found in the system PATH
        print("Error: 'ollama' command not found. Is Ollama installed correctly?")
        return False
    
    except Exception as e:
        # Catch other unexpected exceptions
        print(f"An unexpected error occurred during model pull: {e}")
        return False