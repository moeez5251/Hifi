# watcher.py
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
class ReloadHandler(FileSystemEventHandler):
    def __init__(self, file_to_run):
        self.file_to_run = file_to_run
        self.process = subprocess.Popen(["python", self.file_to_run])

    def on_any_event(self, event):
        print("Changes detected. Reloading...")
        self.process.kill()
        self.process = subprocess.Popen(["python", self.file_to_run])

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
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
