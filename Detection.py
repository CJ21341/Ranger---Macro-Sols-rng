import os
import time
import threading
import json

CONFIG_FILE = "config.json"

class RobloxLogWatcher:
    """
    Watches the Roblox log folder for new log lines and triggers a callback.
    Only reacts to new lines after the watcher starts.
    """

    def __init__(self, log_folder, signal_callback):
        self.log_folder = log_folder
        self.signal_callback = signal_callback

        self.current_file = None
        self.file_handle = None
        self.file_position = 0

        self.stop_flag = False

    def load_triggers(self):
        """Load enabled biomes from config.json"""
        if not os.path.exists(CONFIG_FILE):
            return []

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            biomes_config = config.get("biomes", {})
            
            return [biome for biome, enabled in biomes_config.items() if enabled]
        except Exception as e:
            print("[Watcher] Failed to load triggers:", e)
            return []

    def start(self):
        """Start the watcher in a background thread"""
        self.stop_flag = False
        threading.Thread(target=self.run, daemon=True).start()
        print("[LogWatcher] Started.")

    def stop(self):
        """Stop the watcher"""
        self.stop_flag = True
        if self.file_handle:
            self.file_handle.close()
        print("[LogWatcher] Stopped.")

    def run(self):
        """Main watcher loop"""
        while not self.stop_flag:
            try:
                latest_file = self.get_latest_log_file()
                if latest_file != self.current_file:
                    self.current_file = latest_file
                    if self.file_handle:
                        self.file_handle.close()
                    if self.current_file:
                        self.file_handle = open(self.current_file, "r", encoding="utf-8")
                     
                        self.file_handle.seek(0, os.SEEK_END)
                        print(f"[Watcher] Watching new file: {self.current_file}")

                if self.file_handle:
                    self.watch_file(self.file_handle)
            except Exception as e:
                print("[Watcher Error]", e)
            time.sleep(0.2)

    def get_latest_log_file(self):
        """Return the most recently modified .log file"""
        log_files = sorted(
            [f for f in os.listdir(self.log_folder) if f.endswith(".log")],
            key=lambda x: os.path.getmtime(os.path.join(self.log_folder, x)),
            reverse=True
        )
        return os.path.join(self.log_folder, log_files[0]) if log_files else None

    def watch_file(self, file_handle):
        """Read new lines from the file and trigger callback"""
        line = file_handle.readline()
        while line:
            line = line.strip()
            if line:
                self.process_line(line)
            line = file_handle.readline()

    def process_line(self, line):
        """Process each log line"""
        triggers = self.load_triggers() 
        for biome in triggers:
            if biome.lower() in line.lower():
                self.signal_callback(biome, line)
