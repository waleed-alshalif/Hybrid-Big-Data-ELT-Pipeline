import time
import threading
import psutil

class SystemMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.running = False
        self.thread = None

    def _monitor(self):
        while self.running:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            print(f"📡 [System Telemetry] CPU: {cpu:5.1f}% | RAM Used: {mem.percent:5.1f}% ({mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB)")
            time.sleep(self.interval)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)