import subprocess
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
class ReloadHandler(FileSystemEventHandler):
    def __init__(self, file_to_run):
        self.file_to_run = file_to_run

        # Explicitly use the Python executable from the virtual environment
        python_path = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')

        # Run the script in the background using the virtual environment's Python interpreter
        self.process = subprocess.Popen(
            [python_path, self.file_to_run], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )

    def on_any_event(self, event):
        print("Changes detected. Reloading...")
        self.process.kill()
        # Restart the script using the virtual environment's Python interpreter
        python_path = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
        self.process = subprocess.Popen(
            [python_path, self.file_to_run], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )

    def read_output(self):
        # Reading stdout and stderr
        stdout, stderr = self.process.communicate()
        if stdout:
            print(stdout.decode("utf-8"))
        if stderr:
            print("Error:", stderr.decode("utf-8"))

if __name__ == "__main__":
    path = "."  # current directory
    file_to_run = "main.py"

    event_handler = ReloadHandler(file_to_run)
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            event_handler.read_output()  # Read process output
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
