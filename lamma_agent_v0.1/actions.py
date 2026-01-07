import subprocess
import os
import webbrowser
from pathlib import Path

def open_browser(site_name=None):
    """Smarter browser opener: handles 'google', 'instagram', etc."""
    if not site_name:
        subprocess.Popen(['start', 'chrome'], shell=True)
        return "Opening Chrome..."
    
    url = site_name.lower()
    if "." not in url:
        url = f"{url}.com"
    if not url.startswith("http"):
        url = f"https://{url}"
        
    webbrowser.open(url)
    return f"Navigating to {url}..."


def create_local_file(details_json):
    """Expects a dict with 'filename', 'folder', and 'content'."""
    try:
        folder_path = Path(details_json.get("folder", ".")).resolve()
        filename = details_json.get("filename", "new_file.txt")
        content = details_json.get("content", "")

        if not os.path.exists(folder_path.anchor):
            return f"Error: Drive {folder_path.anchor} not found. Please check the drive letter."

        folder_path.mkdir(parents=True, exist_ok=True)
            
        file_full_path = folder_path / filename
        
        with open(file_full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully created {filename} at {file_full_path}"
    except PermissionError:
        return "Permission Denied: Try running your terminal/IDE as Administrator to write to this location."
    except Exception as e:
        return f"File Error: {str(e)}"


def open_cmd(command=None):
    if command:
        full_command = f'start cmd /k "{command}"'
        
        subprocess.Popen(full_command, shell=True)
        return f"Executing in CMD: {command}"
    
    subprocess.Popen('start cmd', shell=True)
    return "Opened Command Prompt"

ACTION_MAP = {
    "open_browser": open_browser,
    "create_file": create_local_file,
    "open_cmd": open_cmd
}