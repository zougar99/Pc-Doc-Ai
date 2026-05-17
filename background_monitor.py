"""
PC Doctor AI - Background Monitor
Runs in the background and monitors system health in real-time.
"""

import psutil
import time
import os
import sys
from datetime import datetime
from threading import Thread, Event

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    RICH_AVAILABLE = True
except:
    RICH_AVAILABLE = False
    print = lambda *args, **kwargs: None


class BackgroundMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.stop_event = Event()
        self.alerts = []
        self.cpu_history = []
        self.memory_history = []
        self.disk_history = []

    def check_cpu(self):
        cpu = psutil.cpu_percent(interval=1)
        self.cpu_history.append(cpu)
        if len(self.cpu_history) > 20:
            self.cpu_history.pop(0)

        if cpu > 90:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "CPU",
                "severity": "critical",
                "message": f"CPU usage at {cpu:.1f}% - System overload!",
                "fix": "Close heavy processes in Task Manager"
            })
        elif cpu > 75:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "CPU",
                "severity": "warning",
                "message": f"CPU usage high at {cpu:.1f}%",
                "fix": "Monitor processes"
            })
        return cpu

    def check_memory(self):
        mem = psutil.virtual_memory()
        percent = mem.percent
        self.memory_history.append(percent)
        if len(self.memory_history) > 20:
            self.memory_history.pop(0)

        if percent > 90:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "Memory",
                "severity": "critical",
                "message": f"RAM at {percent:.1f}% - Low memory!",
                "fix": "Close applications or restart PC"
            })
        elif percent > 75:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "Memory",
                "severity": "warning",
                "message": f"RAM usage high at {percent:.1f}%",
                "fix": "Check memory in Task Manager"
            })
        return percent

    def check_disk(self):
        disk = psutil.disk_usage('C:')
        percent = disk.percent
        self.disk_history.append(percent)
        if len(self.disk_history) > 20:
            self.disk_history.pop(0)

        if percent > 95:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "Disk",
                "severity": "critical",
                "message": f"Disk C: at {percent:.1f}% - Nearly full!",
                "fix": "Free up space immediately"
            })
        elif percent > 85:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "Disk",
                "severity": "warning",
                "message": f"Disk C: at {percent:.1f}% - Getting full",
                "fix": "Run Disk Cleanup"
            })
        return percent

    def check_network(self):
        net = psutil.net_io_counters()
        return net

    def check_temperature(self):
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current > 0 and entry.current < 150:
                            return entry.current
        except:
            pass
        return None

    def monitor_loop(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting background monitoring...")
        print(f"Monitoring interval: {self.interval} seconds")
        print("Press Ctrl+C to stop\n")

        while not self.stop_event.is_set():
            try:
                cpu = self.check_cpu()
                mem = self.check_memory()
                disk = self.check_disk()
                temp = self.check_temperature()

                if RICH_AVAILABLE:
                    console.clear()
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] System Status:")
                    print(f"CPU: {cpu:.1f}% | Memory: {mem:.1f}% | Disk: {disk:.1f}%")
                    if temp:
                        print(f"Temp: {temp:.1f}°C")

                    if self.alerts:
                        print("\n--- ALERTS ---")
                        for a in self.alerts[-5:]:
                            print(f"[{a['time']}] {a['type']}: {a['message']}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] CPU:{cpu:.0f}% MEM:{mem:.0f}% DISK:{disk:.0f}%")

                time.sleep(self.interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(self.interval)

        print("\nMonitoring stopped.")

    def start(self):
        monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread


def run_background_mode(interval=5):
    print("=" * 50)
    print("   PC DIAGNOSTIC - BACKGROUND MONITOR")
    print("=" * 50)
    print("\nMonitoring system in real-time...")
    print("Shows CPU, Memory, Disk usage every", interval, "seconds")
    print("Alerts when values are critical\n")

    monitor = BackgroundMonitor(interval)
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", "-i", type=int, default=5, help="Check interval in seconds")
    args = parser.parse_args()

    run_background_mode(args.interval)