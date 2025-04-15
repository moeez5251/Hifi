import subprocess
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, file_to_run):
        self.file_to_run = file_to_run
        self.process = None
        self.last_modified = time.time()
        self.python_path = os.path.join(os.getcwd(), 'venv', 'Scripts', 'python.exe')
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.kill()

        print(f"\n🔁 Restarting {self.file_to_run}...\n")
        self.process = subprocess.Popen(
            [self.python_path, self.file_to_run],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )

        # Start a thread to read the output
        threading.Thread(target=self.read_output, daemon=True).start()

    def read_output(self):
        for line in self.process.stdout:
            print(line.strip())

    def on_modified(self, event):
        if event.src_path.endswith(".py") or event.src_path.endswith(".css"):
            now = time.time()
            if now - self.last_modified > 0.5:
                self.last_modified = now
                self.start_process()

if __name__ == "__main__":
    path = "."  # Watch current directory
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
