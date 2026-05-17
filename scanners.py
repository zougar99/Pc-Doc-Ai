"""
PC System Scanners - Comprehensive hardware and software diagnostic modules.
Scans CPU, Memory, Disk, Network, GPU, Security, Processes, and Event Logs.
"""

import psutil
import platform
import socket
import subprocess
import os
import sys
import time
import ctypes
import winreg
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False


# ─── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class Issue:
    category: str
    severity: str  # "critical", "warning", "info"
    title: str
    description: str
    recommendation: str


@dataclass
class ScanResult:
    category: str
    data: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    health_score: float = 100.0


# ─── CPU Scanner ────────────────────────────────────────────────────────────────

class CPUScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="CPU")
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            avg_usage = sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0

            result.data = {
                "processor": platform.processor(),
                "architecture": platform.machine(),
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "current_frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else "N/A",
                "max_frequency_mhz": round(cpu_freq.max, 2) if cpu_freq and cpu_freq.max else "N/A",
                "average_usage_percent": round(avg_usage, 1),
                "per_core_usage": [round(x, 1) for x in cpu_percent],
            }

            temps = self._get_cpu_temperature()
            if temps:
                result.data["temperature_celsius"] = temps

            if avg_usage > 85:
                result.issues.append(Issue(
                    "CPU", "critical", "CPU Usage Critical",
                    f"Average CPU usage is {avg_usage:.1f}% — system is overloaded and may freeze or lag.",
                    "Open Task Manager (Ctrl+Shift+Esc), sort by CPU, and close heavy processes. Run a full antivirus scan to check for crypto miners."
                ))
                result.health_score -= 35
            elif avg_usage > 60:
                result.issues.append(Issue(
                    "CPU", "warning", "High CPU Usage",
                    f"Average CPU usage is {avg_usage:.1f}% — system is under significant load. Normal idle is 5-20%.",
                    "Close unnecessary browser tabs and background apps. Check Task Manager for processes using excessive CPU."
                ))
                result.health_score -= 20
            elif avg_usage > 40:
                result.issues.append(Issue(
                    "CPU", "info", "Moderate CPU Usage",
                    f"CPU usage is {avg_usage:.1f}% — higher than typical idle (5-20%).",
                    "Monitor if usage stays high. Background updates or indexing may be running."
                ))
                result.health_score -= 5

            if temps and temps > 80:
                result.issues.append(Issue(
                    "CPU", "critical", "CPU Overheating",
                    f"CPU temperature is {temps}°C — risk of thermal throttling and hardware damage.",
                    "1) Clean dust from CPU cooler 2) Reapply thermal paste 3) Improve case airflow 4) Check if CPU fan is working."
                ))
                result.health_score -= 30
            elif temps and temps > 65:
                result.issues.append(Issue(
                    "CPU", "warning", "CPU Temperature Elevated",
                    f"CPU temperature is {temps}°C (safe range is 30-65°C under normal use).",
                    "Check ventilation, clean dust, ensure fans are spinning properly."
                ))
                result.health_score -= 12

            high_cores = [i for i, u in enumerate(cpu_percent) if u > 90]
            if len(high_cores) > len(cpu_percent) // 3:
                result.issues.append(Issue(
                    "CPU", "warning", "Multiple Cores Under Heavy Load",
                    f"{len(high_cores)} out of {len(cpu_percent)} cores above 90% — CPU is being pushed hard.",
                    "A demanding process or malware may be consuming excessive CPU resources."
                ))
                result.health_score -= 12

            if cpu_freq and cpu_freq.max and cpu_freq.current < cpu_freq.max * 0.5:
                result.issues.append(Issue(
                    "CPU", "info", "CPU Running Below Max Speed",
                    f"CPU at {cpu_freq.current:.0f} MHz vs max {cpu_freq.max:.0f} MHz — may be power-throttled.",
                    "Set power plan to 'High Performance' in Control Panel > Power Options."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("CPU", "warning", "Scan Error", str(e), ""))
        return result

    def _get_cpu_temperature(self) -> Optional[float]:
        try:
            if WMI_AVAILABLE:
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w.Sensor()
                for sensor in sensors:
                    if sensor.SensorType == "Temperature" and "CPU" in sensor.Name:
                        return float(sensor.Value)
        except Exception:
            pass
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current > 0:
                            return entry.current
        except Exception:
            pass
        return None


# ─── Memory Scanner ─────────────────────────────────────────────────────────────

class MemoryScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Memory")
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            avail_gb = round(mem.available / (1024**3), 2)
            used_gb = round(mem.used / (1024**3), 1)
            total_gb = round(mem.total / (1024**3), 1)

            result.data = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": avail_gb,
                "used_gb": round(mem.used / (1024**3), 2),
                "usage_percent": mem.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_gb": round(swap.used / (1024**3), 2),
                "swap_usage_percent": swap.percent,
            }

            if mem.percent > 85:
                result.issues.append(Issue(
                    "Memory", "critical", "RAM Critically Full",
                    f"RAM usage at {mem.percent}% — using {used_gb}GB out of {total_gb}GB with only {avail_gb}GB free. "
                    f"System will slow down severely and apps may crash.",
                    "1) Close browser tabs (each uses 100-500MB) 2) Close unused applications 3) Restart your PC to clear memory leaks 4) Consider upgrading RAM."
                ))
                result.health_score -= 35
            elif mem.percent > 70:
                result.issues.append(Issue(
                    "Memory", "warning", "High RAM Usage",
                    f"RAM usage at {mem.percent}% — {used_gb}GB used, {avail_gb}GB available. "
                    f"Multitasking performance will suffer.",
                    "Close browser tabs and background applications. Check Task Manager > Memory column to find memory hogs."
                ))
                result.health_score -= 18
            elif mem.percent > 55:
                result.issues.append(Issue(
                    "Memory", "info", "Moderate RAM Usage",
                    f"RAM usage at {mem.percent}% — {avail_gb}GB available.",
                    "Usage is acceptable but monitor for increases."
                ))
                result.health_score -= 3

            if avail_gb < 1.5:
                result.issues.append(Issue(
                    "Memory", "critical", "Very Low Available RAM",
                    f"Only {avail_gb}GB RAM available — applications may crash or freeze.",
                    "Immediately close heavy applications. Restart your PC to free up memory."
                ))
                result.health_score -= 20
            elif avail_gb < 3:
                result.issues.append(Issue(
                    "Memory", "warning", "Low Available RAM",
                    f"Only {avail_gb}GB RAM available — limited room for new applications.",
                    "Close unused programs to free up memory."
                ))
                result.health_score -= 10

            if mem.total < 4 * (1024**3):
                result.issues.append(Issue(
                    "Memory", "warning", "Insufficient Total RAM",
                    f"System has only {total_gb}GB RAM — below minimum for modern Windows (8GB recommended).",
                    "Upgrade to at least 8GB RAM. This is the single biggest improvement you can make."
                ))
                result.health_score -= 20
            elif mem.total < 8 * (1024**3):
                result.issues.append(Issue(
                    "Memory", "info", "Limited RAM",
                    f"System has {total_gb}GB RAM. 16GB is recommended for smooth multitasking.",
                    "Consider upgrading to 16GB if you use many apps simultaneously."
                ))
                result.health_score -= 5

            if swap.percent > 60:
                result.issues.append(Issue(
                    "Memory", "warning", "Heavy Swap/Pagefile Usage",
                    f"Swap at {swap.percent}% ({round(swap.used / (1024**3), 1)}GB) — system is using slow disk as memory, causing major slowdowns.",
                    "This means RAM is insufficient for your workload. Close applications or upgrade RAM."
                ))
                result.health_score -= 15

        except Exception as e:
            result.issues.append(Issue("Memory", "warning", "Scan Error", str(e), ""))
        return result


# ─── Disk Scanner ───────────────────────────────────────────────────────────────

class DiskScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Disk")
        try:
            partitions = psutil.disk_partitions()
            disk_io = psutil.disk_io_counters()
            disks_info = []

            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    free_gb = round(usage.free / (1024**3), 1)
                    total_gb = round(usage.total / (1024**3), 2)
                    disk_data = {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "filesystem": part.fstype,
                        "total_gb": total_gb,
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": usage.percent,
                    }
                    disks_info.append(disk_data)

                    is_system = part.mountpoint.upper().startswith("C")

                    if usage.percent > 90:
                        result.issues.append(Issue(
                            "Disk", "critical", f"Drive {part.mountpoint} Critically Full",
                            f"{part.mountpoint} is {usage.percent}% full with only {free_gb}GB free. "
                            f"{'Windows needs at least 10-15GB free on C: to function properly. System may crash or fail to update.' if is_system else 'Drive is almost completely full.'}",
                            "1) Run Disk Cleanup (search 'Disk Cleanup' in Start) 2) Empty Recycle Bin 3) Clear browser cache "
                            "4) Uninstall unused programs 5) Move large files to external storage."
                        ))
                        result.health_score -= 30
                    elif usage.percent > 80:
                        result.issues.append(Issue(
                            "Disk", "warning", f"Drive {part.mountpoint} Getting Full",
                            f"{part.mountpoint} is {usage.percent}% full ({free_gb}GB free). "
                            f"{'Low space on system drive affects Windows performance, updates, and swap file.' if is_system else 'Running low on storage space.'}",
                            "Clean up disk space: delete temp files, old downloads, unused programs. Use 'Settings > Storage' to see what's using space."
                        ))
                        result.health_score -= 15

                    if free_gb < 10 and is_system:
                        result.issues.append(Issue(
                            "Disk", "critical", f"Critically Low Space on System Drive ({part.mountpoint})",
                            f"Only {free_gb}GB free on system drive. Windows needs 10-15GB minimum to run properly. "
                            f"Updates will fail, swap file cannot grow, and system may freeze.",
                            "URGENT: Free up space immediately. Clear temp files, empty trash, uninstall unused programs."
                        ))
                        result.health_score -= 25
                    elif free_gb < 20 and is_system:
                        result.issues.append(Issue(
                            "Disk", "warning", f"Low Free Space on System Drive ({part.mountpoint})",
                            f"Only {free_gb}GB free on C: drive. Recommended minimum is 20GB for smooth operation.",
                            "Free up space to prevent performance issues and update failures."
                        ))
                        result.health_score -= 10
                    elif free_gb < 5 and not is_system:
                        result.issues.append(Issue(
                            "Disk", "warning", f"Very Low Space on {part.mountpoint}",
                            f"Only {free_gb}GB free on {part.mountpoint}.",
                            "Move or delete files to free up space."
                        ))
                        result.health_score -= 8

                except PermissionError:
                    continue
                except OSError as e:
                    error_msg = str(e)
                    result.issues.append(Issue(
                        "Disk", "critical", f"Disk I/O Error on {part.mountpoint}",
                        f"Cannot read drive {part.mountpoint} — I/O device error: {error_msg}. "
                        f"This could mean the drive is failing, disconnected, or has bad sectors.",
                        "1) If external drive: disconnect and reconnect 2) Run 'chkdsk {0}: /f' as admin 3) Check cables "
                        "4) Back up data IMMEDIATELY if this is your main drive — the disk may be failing.".format(
                            part.mountpoint.replace('\\', '').replace(':', '')
                        )
                    ))
                    result.health_score -= 25

            result.data = {
                "partitions": disks_info,
                "io_read_gb": round(disk_io.read_bytes / (1024**3), 2) if disk_io else "N/A",
                "io_write_gb": round(disk_io.write_bytes / (1024**3), 2) if disk_io else "N/A",
            }

            smart_data = self._check_smart_health()
            if smart_data:
                result.data["smart_status"] = smart_data
                if isinstance(smart_data, dict) and smart_data.get("status", "").lower() not in ("ok", ""):
                    result.issues.append(Issue(
                        "Disk", "critical", "Disk Health Warning (SMART)",
                        f"Disk '{smart_data.get('model', 'Unknown')}' reports status: {smart_data.get('status')}.",
                        "Back up your data immediately. The disk may be failing. Consider replacing the drive."
                    ))
                    result.health_score -= 30

        except Exception as e:
            result.issues.append(Issue("Disk", "warning", "Disk Scan Error", str(e), ""))
        return result

    def _check_smart_health(self) -> Optional[dict]:
        try:
            if WMI_AVAILABLE:
                w = wmi.WMI()
                for disk in w.Win32_DiskDrive():
                    return {
                        "model": disk.Model,
                        "serial": disk.SerialNumber.strip() if disk.SerialNumber else "N/A",
                        "interface": disk.InterfaceType,
                        "status": disk.Status,
                    }
        except Exception:
            pass
        return None


# ─── Network Scanner ────────────────────────────────────────────────────────────

class NetworkScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Network")
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io = psutil.net_io_counters()

            net_interfaces = []
            for name, addrs in interfaces.items():
                iface = {"name": name, "addresses": [], "is_up": False, "speed_mbps": 0}
                if name in stats:
                    iface["is_up"] = stats[name].isup
                    iface["speed_mbps"] = stats[name].speed
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        iface["addresses"].append({"type": "IPv4", "address": addr.address})
                    elif addr.family == socket.AF_INET6:
                        iface["addresses"].append({"type": "IPv6", "address": addr.address})
                net_interfaces.append(iface)

            result.data = {
                "hostname": socket.gethostname(),
                "interfaces": net_interfaces,
                "bytes_sent_gb": round(io.bytes_sent / (1024**3), 2),
                "bytes_recv_gb": round(io.bytes_recv / (1024**3), 2),
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
                "errors_in": io.errin,
                "errors_out": io.errout,
                "drops_in": io.dropin,
                "drops_out": io.dropout,
            }

            connectivity = self._check_connectivity()
            result.data["internet_connected"] = connectivity["connected"]
            result.data["dns_working"] = connectivity["dns_ok"]
            result.data["latency_ms"] = connectivity.get("latency_ms")

            if not connectivity["connected"]:
                result.issues.append(Issue(
                    "Network", "critical", "No Internet Connection",
                    "Unable to reach the internet.",
                    "Check your network cable/WiFi, router, or ISP status."
                ))
                result.health_score -= 30
            elif not connectivity["dns_ok"]:
                result.issues.append(Issue(
                    "Network", "warning", "DNS Resolution Failed",
                    "Internet is reachable but DNS resolution is failing.",
                    "Try changing DNS to 8.8.8.8 or 1.1.1.1."
                ))
                result.health_score -= 15

            if connectivity.get("latency_ms") and connectivity["latency_ms"] > 200:
                result.issues.append(Issue(
                    "Network", "warning", "High Network Latency",
                    f"Network latency is {connectivity['latency_ms']}ms.",
                    "Check for network congestion or contact your ISP."
                ))
                result.health_score -= 10

            if io.errin + io.errout > 100:
                result.issues.append(Issue(
                    "Network", "warning", "Network Errors Detected",
                    f"Input errors: {io.errin}, Output errors: {io.errout}.",
                    "Check network cables, drivers, or adapter settings."
                ))
                result.health_score -= 10

            if io.dropin + io.dropout > 100:
                result.issues.append(Issue(
                    "Network", "warning", "Packet Drops Detected",
                    f"Dropped packets - In: {io.dropin}, Out: {io.dropout}.",
                    "Network congestion or hardware issue possible."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Network", "warning", "Scan Error", str(e), ""))
        return result

    def _check_connectivity(self) -> dict:
        result = {"connected": False, "dns_ok": False, "latency_ms": None}
        try:
            start = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            result["connected"] = True
            result["latency_ms"] = round((time.time() - start) * 1000, 1)
        except (socket.timeout, OSError):
            return result
        try:
            socket.gethostbyname("www.google.com")
            result["dns_ok"] = True
        except socket.gaierror:
            pass
        return result


# ─── GPU Scanner ────────────────────────────────────────────────────────────────

class GPUScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="GPU")
        try:
            gpus_info = []

            if GPUTIL_AVAILABLE:
                gpus = GPUtil.getGPUs()
                for gpu in gpus:
                    gpu_data = {
                        "name": gpu.name,
                        "id": gpu.id,
                        "memory_total_mb": gpu.memoryTotal,
                        "memory_used_mb": gpu.memoryUsed,
                        "memory_free_mb": gpu.memoryFree,
                        "memory_usage_percent": round(gpu.memoryUtil * 100, 1),
                        "gpu_usage_percent": round(gpu.load * 100, 1),
                        "temperature_celsius": gpu.temperature,
                        "driver_version": gpu.driver,
                    }
                    gpus_info.append(gpu_data)

                    if gpu.temperature and gpu.temperature > 90:
                        result.issues.append(Issue(
                            "GPU", "critical", f"GPU {gpu.name} Overheating",
                            f"GPU temperature is {gpu.temperature}°C.",
                            "Improve case airflow, clean GPU fans, or adjust fan curve."
                        ))
                        result.health_score -= 25
                    elif gpu.temperature and gpu.temperature > 80:
                        result.issues.append(Issue(
                            "GPU", "warning", f"GPU {gpu.name} Temperature High",
                            f"GPU temperature is {gpu.temperature}°C.",
                            "Monitor temperature and ensure adequate cooling."
                        ))
                        result.health_score -= 10

                    if gpu.memoryUtil and gpu.memoryUtil > 0.9:
                        result.issues.append(Issue(
                            "GPU", "warning", "GPU Memory Almost Full",
                            f"GPU VRAM usage at {round(gpu.memoryUtil * 100, 1)}%.",
                            "Close GPU-intensive applications."
                        ))
                        result.health_score -= 10

            if not gpus_info and WMI_AVAILABLE:
                try:
                    w = wmi.WMI()
                    for gpu in w.Win32_VideoController():
                        gpus_info.append({
                            "name": gpu.Name,
                            "driver_version": gpu.DriverVersion,
                            "driver_date": gpu.DriverDate,
                            "video_memory_mb": round(int(gpu.AdapterRAM or 0) / (1024**2), 0),
                            "status": gpu.Status,
                        })
                except Exception:
                    pass

            result.data = {"gpus": gpus_info}
            if not gpus_info:
                result.data["note"] = "No dedicated GPU detected or GPU libraries not available."

        except Exception as e:
            result.issues.append(Issue("GPU", "warning", "Scan Error", str(e), ""))
        return result


# ─── Process Scanner ────────────────────────────────────────────────────────────

class ProcessScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Processes")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    info = proc.info
                    if info['cpu_percent'] is not None:
                        processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            total_processes = len(processes)
            top_cpu = sorted(processes, key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)[:10]
            top_memory = sorted(processes, key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)[:10]

            zombie_procs = [p for p in processes if p.get('status') == 'zombie']

            result.data = {
                "total_processes": total_processes,
                "top_cpu_consumers": [
                    {"pid": p['pid'], "name": p['name'], "cpu_percent": round(p.get('cpu_percent', 0) or 0, 1)}
                    for p in top_cpu
                ],
                "top_memory_consumers": [
                    {"pid": p['pid'], "name": p['name'], "memory_percent": round(p.get('memory_percent', 0) or 0, 1)}
                    for p in top_memory
                ],
                "zombie_processes": len(zombie_procs),
            }

            if total_processes > 250:
                result.issues.append(Issue(
                    "Processes", "warning", "Many Running Processes",
                    f"{total_processes} processes running — this is high and uses extra memory.",
                    "Disable unnecessary startup programs in Task Manager > Startup tab."
                ))
                result.health_score -= 8
            elif total_processes > 180:
                result.issues.append(Issue(
                    "Processes", "info", "High Process Count",
                    f"{total_processes} processes running.",
                    "Review startup programs and close unnecessary background apps."
                ))
                result.health_score -= 3

            for p in top_cpu[:5]:
                cpu = p.get('cpu_percent', 0) or 0
                if cpu > 30:
                    result.issues.append(Issue(
                        "Processes", "warning", f"High CPU: {p['name']}",
                        f"'{p['name']}' (PID {p['pid']}) using {cpu:.1f}% CPU.",
                        f"Open Task Manager, find '{p['name']}', and decide if it should be closed or restarted."
                    ))
                    result.health_score -= 8

            for p in top_memory[:5]:
                mem = p.get('memory_percent', 0) or 0
                if mem > 10:
                    total_ram = psutil.virtual_memory().total / (1024**3)
                    used_mb = round(mem / 100 * total_ram * 1024, 0)
                    result.issues.append(Issue(
                        "Processes", "warning", f"Memory Hog: {p['name']}",
                        f"'{p['name']}' (PID {p['pid']}) using {mem:.1f}% RAM (~{used_mb:.0f}MB). This is a significant share of total memory.",
                        f"Restart '{p['name']}' if possible. If it's a browser, close excess tabs."
                    ))
                    result.health_score -= 8
                elif mem > 5:
                    result.issues.append(Issue(
                        "Processes", "info", f"Notable Memory: {p['name']}",
                        f"'{p['name']}' (PID {p['pid']}) using {mem:.1f}% RAM.",
                        f"Normal for some apps, but monitor if it keeps growing (possible memory leak)."
                    ))
                    result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("Processes", "warning", "Scan Error", str(e), ""))
        return result


# ─── Security Scanner ───────────────────────────────────────────────────────────

class SecurityScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Security")
        try:
            firewall = self._check_firewall()
            defender = self._check_windows_defender()
            uac = self._check_uac()
            updates = self._check_windows_update()

            result.data = {
                "firewall_enabled": firewall,
                "windows_defender": defender,
                "uac_enabled": uac,
                "pending_updates": updates,
                "is_admin": ctypes.windll.shell32.IsUserAnAdmin() != 0,
            }

            if not firewall:
                result.issues.append(Issue(
                    "Security", "critical", "Firewall Disabled",
                    "Windows Firewall appears to be disabled.",
                    "Enable Windows Firewall in Control Panel > System and Security."
                ))
                result.health_score -= 25

            if defender:
                if not defender.get("enabled", True):
                    result.issues.append(Issue(
                        "Security", "critical", "Windows Defender Disabled",
                        "Antivirus is not active — your PC is unprotected against malware, viruses, and ransomware.",
                        "Open Windows Security > Virus & Threat Protection and enable all protections. Or install an alternative antivirus."
                    ))
                    result.health_score -= 30
                if not defender.get("realtime_protection", True):
                    result.issues.append(Issue(
                        "Security", "critical", "Real-Time Protection OFF",
                        "Windows Defender Real-Time Protection is disabled. Your PC is NOT scanning files as they are opened, "
                        "leaving you vulnerable to malware, ransomware, and viruses.",
                        "Open Windows Security > Virus & Threat Protection > Manage Settings > Turn ON Real-time protection."
                    ))
                    result.health_score -= 25

            if not uac:
                result.issues.append(Issue(
                    "Security", "warning", "UAC May Be Disabled",
                    "User Account Control might not be active.",
                    "Enable UAC in Control Panel for better security."
                ))
                result.health_score -= 10

        except Exception as e:
            result.issues.append(Issue("Security", "warning", "Scan Error", str(e), ""))
        return result

    def _check_firewall(self) -> bool:
        try:
            output = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles", "state"],
                capture_output=True, text=True, timeout=10
            )
            return "ON" in output.stdout.upper()
        except Exception:
            return True

    def _check_windows_defender(self) -> dict:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-MpComputerStatus | Select-Object -Property AntivirusEnabled,RealTimeProtectionEnabled,AntivirusSignatureLastUpdated | ConvertTo-Json"],
                capture_output=True, text=True, timeout=15
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                return {
                    "enabled": data.get("AntivirusEnabled", False),
                    "realtime_protection": data.get("RealTimeProtectionEnabled", False),
                    "last_signature_update": data.get("AntivirusSignatureLastUpdated"),
                }
        except Exception:
            pass
        return {"enabled": True, "note": "Could not query Defender status"}

    def _check_uac(self) -> bool:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            value, _ = winreg.QueryValueEx(key, "EnableLUA")
            winreg.CloseKey(key)
            return value == 1
        except Exception:
            return True

    def _check_windows_update(self) -> Optional[str]:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject Microsoft.Update.AutoUpdate).Results | Select-Object -Property LastInstallationSuccessDate | ConvertTo-Json"],
                capture_output=True, text=True, timeout=15
            )
            if output.returncode == 0:
                return output.stdout.strip()
        except Exception:
            pass
        return None


# ─── System Info Scanner ────────────────────────────────────────────────────────

class SystemScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="System")
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time

            result.data = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "os_edition": platform.platform(),
                "hostname": platform.node(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                "uptime_hours": round(uptime.total_seconds() / 3600, 1),
                "uptime_human": str(timedelta(seconds=int(uptime.total_seconds()))),
            }

            if WMI_AVAILABLE:
                try:
                    w = wmi.WMI()
                    for os_info in w.Win32_OperatingSystem():
                        result.data["os_name"] = os_info.Caption
                        result.data["build_number"] = os_info.BuildNumber
                        result.data["registered_user"] = os_info.RegisteredUser
                    for bios in w.Win32_BIOS():
                        result.data["bios_version"] = bios.SMBIOSBIOSVersion
                        result.data["bios_manufacturer"] = bios.Manufacturer
                    for board in w.Win32_BaseBoard():
                        result.data["motherboard"] = board.Product
                        result.data["motherboard_manufacturer"] = board.Manufacturer
                except Exception:
                    pass

            if uptime.total_seconds() > 5 * 24 * 3600:
                result.issues.append(Issue(
                    "System", "warning", "Long Uptime — Restart Needed",
                    f"System has been running for {result.data['uptime_human']} without a restart. "
                    f"Memory leaks accumulate, pending updates are not applied, and performance degrades over time.",
                    "Restart your PC to apply updates, clear memory, and refresh the system."
                ))
                result.health_score -= 12
            elif uptime.total_seconds() > 3 * 24 * 3600:
                result.issues.append(Issue(
                    "System", "info", "System Running for Multiple Days",
                    f"Uptime: {result.data['uptime_human']}. A restart helps keep the system fresh.",
                    "Consider restarting soon to apply pending updates and free accumulated memory."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("System", "warning", "Scan Error", str(e), ""))
        return result


# ─── Battery Scanner ────────────────────────────────────────────────────────────

class BatteryScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Battery")
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                result.data = {"present": False, "note": "No battery detected (desktop PC)."}
                return result

            result.data = {
                "present": True,
                "percent": battery.percent,
                "plugged_in": battery.power_plugged,
                "time_remaining_min": round(battery.secsleft / 60, 1) if battery.secsleft > 0 else "Calculating...",
            }

            if battery.percent < 15 and not battery.power_plugged:
                result.issues.append(Issue(
                    "Battery", "critical", "Battery Very Low",
                    f"Battery at {battery.percent}% and not charging.",
                    "Connect charger immediately to prevent data loss."
                ))
                result.health_score -= 20
            elif battery.percent < 30 and not battery.power_plugged:
                result.issues.append(Issue(
                    "Battery", "warning", "Battery Low",
                    f"Battery at {battery.percent}%.",
                    "Consider connecting the charger."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Battery", "warning", "Scan Error", str(e), ""))
        return result


# ─── Startup Programs Scanner ───────────────────────────────────────────────────

class StartupScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Startup")
        try:
            startup_items = []
            reg_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]

            for hive, path in reg_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_items.append({"name": name, "command": value})
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    continue

            result.data = {
                "startup_programs": startup_items,
                "count": len(startup_items),
            }

            if len(startup_items) > 15:
                result.issues.append(Issue(
                    "Startup", "warning", "Too Many Startup Programs",
                    f"{len(startup_items)} programs run at startup.",
                    "Disable unnecessary startup programs in Task Manager > Startup tab."
                ))
                result.health_score -= 10
            elif len(startup_items) > 8:
                result.issues.append(Issue(
                    "Startup", "info", "Multiple Startup Programs",
                    f"{len(startup_items)} programs run at startup.",
                    "Review startup programs and disable ones you don't need."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Startup", "warning", "Scan Error", str(e), ""))
        return result


# ─── Event Log Scanner ──────────────────────────────────────────────────────────

class EventLogScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Event Logs")
        try:
            sys_errors = self._get_event_errors("System", 7)
            app_errors = self._get_event_errors("Application", 7)
            bsod_count = self._check_bsod_history()
            app_crashes = self._check_app_crashes()

            all_errors = sys_errors + app_errors
            result.data = {
                "system_errors_7d": len(sys_errors),
                "app_errors_7d": len(app_errors),
                "recent_errors": all_errors[:30],
                "total_recent_errors": len(all_errors),
                "bsod_count_30d": bsod_count,
                "app_crashes_7d": len(app_crashes),
                "recent_crashes": app_crashes[:10],
            }

            if bsod_count > 0:
                result.issues.append(Issue(
                    "Event Logs", "critical", f"{bsod_count} Blue Screen (BSOD) in Last 30 Days",
                    f"Your PC has crashed with a Blue Screen of Death {bsod_count} time(s) recently. "
                    f"This indicates serious hardware or driver problems.",
                    "1) Update all drivers (especially GPU and chipset) 2) Run 'sfc /scannow' as admin "
                    "3) Run 'DISM /Online /Cleanup-Image /RestoreHealth' 4) Check RAM with Windows Memory Diagnostic 5) Check disk with 'chkdsk /f'."
                ))
                result.health_score -= 30

            if len(app_crashes) > 3:
                crash_names = list(set(c.get("app", "Unknown") for c in app_crashes[:5]))
                result.issues.append(Issue(
                    "Event Logs", "warning", f"{len(app_crashes)} Application Crashes (Last 7 Days)",
                    f"Applications crashing frequently: {', '.join(crash_names[:3])}.",
                    "Update or reinstall the crashing applications. Run 'sfc /scannow' to check system files."
                ))
                result.health_score -= 15

            if len(sys_errors) > 30:
                result.issues.append(Issue(
                    "Event Logs", "warning", f"{len(sys_errors)} System Errors (Last 7 Days)",
                    f"High number of system-level errors in Event Viewer. Common sources: "
                    f"{', '.join(list(set(e.get('source', '') for e in sys_errors[:10]))[:4])}.",
                    "Open Event Viewer (eventvwr.msc) > Windows Logs > System to review. Look for recurring errors."
                ))
                result.health_score -= 12
            elif len(sys_errors) > 10:
                result.issues.append(Issue(
                    "Event Logs", "info", f"{len(sys_errors)} System Errors (Last 7 Days)",
                    "Some system errors detected. A few are normal, but many recurring ones indicate problems.",
                    "Review Event Viewer for patterns."
                ))
                result.health_score -= 5

            if len(app_errors) > 20:
                result.issues.append(Issue(
                    "Event Logs", "warning", f"{len(app_errors)} Application Errors (Last 7 Days)",
                    "Many application-level errors logged. Software may be malfunctioning.",
                    "Update your applications. Reinstall any that crash frequently."
                ))
                result.health_score -= 10

            disk_errors = [e for e in sys_errors if any(k in e.get("source", "").lower() for k in ("disk", "ntfs", "volsnap", "iastor"))]
            if disk_errors:
                result.issues.append(Issue(
                    "Event Logs", "critical", f"Disk Errors in System Log ({len(disk_errors)} events)",
                    f"Disk-related errors found from: {', '.join(set(e.get('source', '') for e in disk_errors[:5]))}. "
                    f"This may indicate a failing hard drive.",
                    "BACK UP YOUR DATA. Run 'chkdsk C: /f' as administrator. Consider replacing the drive if errors persist."
                ))
                result.health_score -= 20

        except Exception as e:
            result.issues.append(Issue("Event Logs", "info", "Event Log Scan Limited", str(e), ""))
        return result

    def _get_event_errors(self, log_name, days) -> list:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 f'Get-EventLog -LogName {log_name} -EntryType Error -After (Get-Date).AddDays(-{days}) -Newest 100 2>$null | '
                 f'Select-Object TimeGenerated,Source,Message | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=30
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                return [
                    {"time": str(e.get("TimeGenerated", "")), "source": e.get("Source", ""),
                     "message": str(e.get("Message", ""))[:300]}
                    for e in data
                ]
        except Exception:
            pass
        return []

    def _check_bsod_history(self) -> int:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-EventLog -LogName System -After (Get-Date).AddDays(-30) 2>$null | '
                 'Where-Object {$_.EventID -eq 1001 -and $_.Source -eq "BugCheck"} | Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True, text=True, timeout=20
            )
            if output.returncode == 0 and output.stdout.strip():
                return int(output.stdout.strip())
        except Exception:
            pass
        try:
            minidump = r"C:\Windows\Minidump"
            if os.path.exists(minidump):
                dumps = [f for f in os.listdir(minidump) if f.endswith(".dmp")]
                recent = 0
                cutoff = time.time() - 30 * 86400
                for d in dumps:
                    try:
                        if os.path.getmtime(os.path.join(minidump, d)) > cutoff:
                            recent += 1
                    except OSError:
                        pass
                return recent
        except Exception:
            pass
        return 0

    def _check_app_crashes(self) -> list:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-EventLog -LogName Application -EntryType Error -After (Get-Date).AddDays(-7) -Newest 50 2>$null | '
                 'Where-Object {$_.Source -eq "Application Error" -or $_.Source -eq "Windows Error Reporting"} | '
                 'Select-Object TimeGenerated,Source,Message | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=20
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                crashes = []
                for e in data:
                    msg = str(e.get("Message", ""))
                    app_name = "Unknown"
                    if "Faulting application name:" in msg:
                        try:
                            app_name = msg.split("Faulting application name:")[1].split(",")[0].strip()
                        except (IndexError, AttributeError):
                            pass
                    crashes.append({"time": str(e.get("TimeGenerated", "")), "app": app_name, "message": msg[:200]})
                return crashes
        except Exception:
            pass
        return []


# ─── Installed Software Scanner ──────────────────────────────────────────────────

class InstalledSoftwareScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Installed Software")
        try:
            programs = []
            reg_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            seen = set()
            for hive, path in reg_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if name and name not in seen:
                                    seen.add(name)
                                    version = ""
                                    publisher = ""
                                    size = ""
                                    install_date = ""
                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    except OSError:
                                        pass
                                    try:
                                        publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                                    except OSError:
                                        pass
                                    try:
                                        size_kb = winreg.QueryValueEx(subkey, "EstimatedSize")[0]
                                        size = f"{round(size_kb / 1024, 1)} MB"
                                    except (OSError, TypeError):
                                        pass
                                    try:
                                        install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                                    except OSError:
                                        pass
                                    programs.append({
                                        "name": name,
                                        "version": version,
                                        "publisher": publisher,
                                        "size": size,
                                        "install_date": install_date,
                                    })
                            except OSError:
                                pass
                            winreg.CloseKey(subkey)
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    continue

            programs.sort(key=lambda x: x["name"].lower())
            result.data = {
                "programs": programs,
                "total_count": len(programs),
            }

            if len(programs) > 150:
                result.issues.append(Issue(
                    "Software", "info", "Many Programs Installed",
                    f"{len(programs)} programs installed. Some may be unused.",
                    "Review installed programs and uninstall ones you no longer need."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Software", "warning", "Scan Error", str(e), ""))
        return result


# ─── Drivers Scanner ─────────────────────────────────────────────────────────────

class DriversScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Drivers")
        try:
            drivers = []
            problem_drivers = []

            if WMI_AVAILABLE:
                w = wmi.WMI()
                for d in w.Win32_PnPSignedDriver():
                    if d.DeviceName:
                        drv = {
                            "name": d.DeviceName,
                            "manufacturer": d.Manufacturer or "Unknown",
                            "version": d.DriverVersion or "N/A",
                            "date": d.DriverDate or "N/A",
                            "status": "OK",
                        }
                        drivers.append(drv)

                for dev in w.Win32_PnPEntity():
                    if dev.ConfigManagerErrorCode and dev.ConfigManagerErrorCode != 0:
                        problem_drivers.append({
                            "name": dev.Name or "Unknown Device",
                            "error_code": dev.ConfigManagerErrorCode,
                            "status": dev.Status,
                            "device_id": dev.DeviceID,
                        })

            result.data = {
                "total_drivers": len(drivers),
                "drivers": drivers[:50],
                "problem_drivers": problem_drivers,
                "problem_count": len(problem_drivers),
            }

            if problem_drivers:
                result.issues.append(Issue(
                    "Drivers", "warning", f"{len(problem_drivers)} Driver Problem(s)",
                    f"Devices with driver issues: {', '.join(d['name'] for d in problem_drivers[:3])}",
                    "Update or reinstall drivers via Device Manager, or download from manufacturer."
                ))
                result.health_score -= 10 * min(len(problem_drivers), 3)

        except Exception as e:
            result.issues.append(Issue("Drivers", "warning", "Scan Error", str(e), ""))
        return result


# ─── Windows Services Scanner ────────────────────────────────────────────────────

class ServicesScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Services")
        try:
            services = []
            stopped_critical = []

            critical_services = {
                "wuauserv": "Windows Update",
                "WinDefend": "Windows Defender",
                "mpssvc": "Windows Firewall",
                "EventLog": "Event Log",
                "Dnscache": "DNS Client",
                "Dhcp": "DHCP Client",
                "LanmanWorkstation": "Workstation",
                "Schedule": "Task Scheduler",
                "SamSs": "Security Accounts Manager",
                "RpcSs": "Remote Procedure Call",
                "PlugPlay": "Plug and Play",
                "Spooler": "Print Spooler",
                "AudioSrv": "Windows Audio",
                "Themes": "Themes",
                "BITS": "Background Intelligent Transfer",
                "CryptSvc": "Cryptographic Services",
            }

            if WMI_AVAILABLE:
                w = wmi.WMI()
                for svc in w.Win32_Service():
                    svc_data = {
                        "name": svc.Name,
                        "display_name": svc.DisplayName,
                        "state": svc.State,
                        "start_mode": svc.StartMode,
                        "is_critical": svc.Name in critical_services,
                    }
                    services.append(svc_data)

                    if svc.Name in critical_services and svc.State != "Running":
                        stopped_critical.append({
                            "name": svc.Name,
                            "display_name": critical_services[svc.Name],
                            "state": svc.State,
                        })

            running = [s for s in services if s["state"] == "Running"]
            stopped = [s for s in services if s["state"] == "Stopped"]

            result.data = {
                "total_services": len(services),
                "running_count": len(running),
                "stopped_count": len(stopped),
                "critical_stopped": stopped_critical,
                "services": services,
            }

            for sc in stopped_critical:
                severity = "critical" if sc["name"] in ("WinDefend", "mpssvc", "RpcSs", "SamSs") else "warning"
                result.issues.append(Issue(
                    "Services", severity, f"{sc['display_name']} Not Running",
                    f"Critical service '{sc['display_name']}' ({sc['name']}) is {sc['state']}.",
                    f"Start the service: Run 'net start {sc['name']}' as Administrator."
                ))
                result.health_score -= 15 if severity == "critical" else 8

        except Exception as e:
            result.issues.append(Issue("Services", "warning", "Scan Error", str(e), ""))
        return result


# ─── Temp Files Scanner ──────────────────────────────────────────────────────────

class TempFilesScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Temp Files")
        try:
            locations = {
                "Windows Temp": os.environ.get("TEMP", r"C:\Windows\Temp"),
                "User Temp": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
                "Prefetch": r"C:\Windows\Prefetch",
                "Recent": os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Recent"),
            }

            total_size = 0
            total_files = 0
            breakdown = {}

            for name, path in locations.items():
                if os.path.exists(path):
                    folder_size = 0
                    file_count = 0
                    try:
                        for dirpath, dirnames, filenames in os.walk(path):
                            for f in filenames:
                                try:
                                    fp = os.path.join(dirpath, f)
                                    folder_size += os.path.getsize(fp)
                                    file_count += 1
                                except (OSError, PermissionError):
                                    continue
                    except (OSError, PermissionError):
                        continue
                    breakdown[name] = {
                        "path": path,
                        "size_mb": round(folder_size / (1024**2), 1),
                        "file_count": file_count,
                    }
                    total_size += folder_size
                    total_files += file_count

            browser_cache = self._get_browser_cache_size()
            if browser_cache:
                breakdown.update(browser_cache)
                for v in browser_cache.values():
                    total_size += v.get("size_mb", 0) * (1024**2)
                    total_files += v.get("file_count", 0)

            result.data = {
                "total_size_mb": round(total_size / (1024**2), 1),
                "total_size_gb": round(total_size / (1024**3), 2),
                "total_files": total_files,
                "breakdown": breakdown,
            }

            if total_size > 2 * (1024**3):
                result.issues.append(Issue(
                    "Temp Files", "warning", "Large Temp Files",
                    f"{round(total_size / (1024**3), 1)}GB of temporary files found.",
                    "Run Disk Cleanup or use the cleanup tool to free space."
                ))
                result.health_score -= 10
            elif total_size > 500 * (1024**2):
                result.issues.append(Issue(
                    "Temp Files", "info", "Temp Files Accumulation",
                    f"{round(total_size / (1024**2), 0)}MB of temporary files found.",
                    "Consider cleaning temp files periodically."
                ))
                result.health_score -= 3

        except Exception as e:
            result.issues.append(Issue("Temp Files", "warning", "Scan Error", str(e), ""))
        return result

    def _get_browser_cache_size(self) -> dict:
        caches = {}
        local = os.environ.get("LOCALAPPDATA", "")
        paths = {
            "Chrome Cache": os.path.join(local, r"Google\Chrome\User Data\Default\Cache"),
            "Edge Cache": os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
            "Firefox Cache": os.path.join(local, r"Mozilla\Firefox\Profiles"),
        }
        for name, path in paths.items():
            if os.path.exists(path):
                size = 0
                count = 0
                try:
                    for dp, dn, fns in os.walk(path):
                        for f in fns:
                            try:
                                size += os.path.getsize(os.path.join(dp, f))
                                count += 1
                            except (OSError, PermissionError):
                                continue
                except (OSError, PermissionError):
                    continue
                if size > 0:
                    caches[name] = {"path": path, "size_mb": round(size / (1024**2), 1), "file_count": count}
        return caches


# ─── Real-Time Monitor ───────────────────────────────────────────────────────────

class RealTimeMonitor:
    """Provides live system stats for the monitoring dashboard."""

    @staticmethod
    def get_snapshot() -> dict:
        cpu_pct = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "cpu_percent": cpu_pct,
            "cpu_per_core": psutil.cpu_percent(percpu=True),
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "net_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "net_recv_mb": round(net.bytes_recv / (1024**2), 1),
        }


# ─── System Tools ────────────────────────────────────────────────────────────────

class SystemTools:
    """Collection of system maintenance and fix tools."""

    @staticmethod
    def clean_temp_files() -> dict:
        """Delete temporary files from common locations."""
        cleaned_size = 0
        cleaned_count = 0
        errors = []

        paths = [
            os.environ.get("TEMP", r"C:\Windows\Temp"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        ]

        for folder in paths:
            if not os.path.exists(folder):
                continue
            for dirpath, dirnames, filenames in os.walk(folder, topdown=False):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        cleaned_size += size
                        cleaned_count += 1
                    except (OSError, PermissionError):
                        continue
                for d in dirnames:
                    try:
                        os.rmdir(os.path.join(dirpath, d))
                    except (OSError, PermissionError):
                        continue

        return {
            "cleaned_files": cleaned_count,
            "freed_mb": round(cleaned_size / (1024**2), 1),
            "errors": errors,
        }

    @staticmethod
    def flush_dns() -> dict:
        try:
            r = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=10)
            return {"success": r.returncode == 0, "output": r.stdout.strip()}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def run_sfc_scan() -> dict:
        try:
            r = subprocess.run(
                ["sfc", "/scannow"], capture_output=True, text=True, timeout=600
            )
            return {"success": r.returncode == 0, "output": r.stdout.strip()[:1000]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def run_disk_cleanup(drive="C") -> dict:
        try:
            subprocess.Popen(["cleanmgr", f"/d", drive])
            return {"success": True, "output": f"Disk Cleanup launched for drive {drive}:"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def check_disk(drive="C") -> dict:
        try:
            r = subprocess.run(
                ["chkdsk", f"{drive}:"], capture_output=True, text=True, timeout=60
            )
            return {"success": True, "output": r.stdout.strip()[:2000]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def reset_network() -> dict:
        results = []
        cmds = [
            (["ipconfig", "/release"], "Release IP"),
            (["ipconfig", "/flushdns"], "Flush DNS"),
            (["ipconfig", "/renew"], "Renew IP"),
            (["netsh", "winsock", "reset"], "Reset Winsock"),
        ]
        for cmd, label in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                results.append(f"{label}: {'OK' if r.returncode == 0 else 'Failed'}")
            except Exception as e:
                results.append(f"{label}: Error - {e}")
        return {"success": True, "output": "\n".join(results)}

    @staticmethod
    def open_device_manager():
        try:
            subprocess.Popen(["devmgmt.msc"])
        except Exception:
            pass

    @staticmethod
    def open_task_manager():
        try:
            subprocess.Popen(["taskmgr"])
        except Exception:
            pass

    @staticmethod
    def open_event_viewer():
        try:
            subprocess.Popen(["eventvwr.msc"])
        except Exception:
            pass

    @staticmethod
    def open_disk_management():
        try:
            subprocess.Popen(["diskmgmt.msc"])
        except Exception:
            pass

    @staticmethod
    def open_system_info():
        try:
            subprocess.Popen(["msinfo32"])
        except Exception:
            pass

    @staticmethod
    def clear_recycle_bin() -> dict:
        try:
            subprocess.run(["powershell", "-Command", "Clear-RecycleBin -Force"], capture_output=True, text=True, timeout=30)
            return {"success": True, "output": "Recycle Bin cleared"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def clear_dns_cache() -> dict:
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=10)
            return {"success": True, "output": "DNS cache flushed"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def restart_explorer() -> dict:
        try:
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], capture_output=True, text=True, timeout=10)
            subprocess.Popen(["explorer.exe"])
            return {"success": True, "output": "Explorer restarted"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def clear_font_cache() -> dict:
        try:
            subprocess.run(["net", "stop", "Windows Font Cache Service"], capture_output=True, text=True, timeout=10)
            font_path = r"C:\Windows\System32\FNTCACHE.DAT"
            if os.path.exists(font_path):
                os.remove(font_path)
            subprocess.run(["net", "start", "Windows Font Cache Service"], capture_output=True, text=True, timeout=10)
            return {"success": True, "output": "Font cache cleared"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def disable_startup_item(program_name: str) -> dict:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, program_name)
            winreg.CloseKey(key)
            return {"success": True, "output": f"Disabled: {program_name}"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def start_service(service_name: str) -> dict:
        try:
            subprocess.run(["net", "start", service_name], capture_output=True, text=True, timeout=30)
            return {"success": True, "output": f"Started: {service_name}"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def run_windows_update() -> dict:
        try:
            subprocess.Popen(["ms-settings:windowsupdate"])
            return {"success": True, "output": "Windows Update opened"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def open_control_panel():
        try:
            subprocess.Popen(["control"])
        except Exception:
            pass

    @staticmethod
    def open_services():
        try:
            subprocess.Popen(["services.msc"])
        except Exception:
            pass

    @staticmethod
    def open_registry_editor():
        try:
            subprocess.Popen(["regedit"])
        except Exception:
            pass

    @staticmethod
    def uninstall_program(program_name: str) -> dict:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 f'Get-WmiObject -Class Win32_Product | Where-Object {{$_.Name -like "*{program_name}*"}} | Uninstall'],
                capture_output=True, text=True, timeout=120
            )
            return {"success": output.returncode == 0, "output": output.stdout.strip()[:500]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def kill_process(pid: int) -> dict:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, text=True, timeout=10)
            return {"success": True, "output": f"Process {pid} terminated"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def create_restore_point() -> dict:
        try:
            subprocess.run(
                ["powershell", "-Command",
                 "Checkpoint-Computer -Description 'PC Diagnostic Tool Restore Point' -RestorePointType 'MODIFY_SETTINGS'"],
                capture_output=True, text=True, timeout=30
            )
            return {"success": True, "output": "Restore point created"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def ping_host(host="8.8.8.8", count=4) -> dict:
        try:
            output = subprocess.run(["ping", "-n", str(count), host], capture_output=True, text=True, timeout=30)
            return {"success": output.returncode == 0, "output": output.stdout.strip()[:500]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def run_system_file_check() -> dict:
        try:
            subprocess.Popen(["cmd", "/c", "sfc /scannow"])
            return {"success": True, "output": "System File Checker started. Run in admin command prompt for full results."}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def disable_windows_features():
        try:
            subprocess.Popen(["optionalfeatures"])
        except Exception:
            pass

    @staticmethod
    def open_power_options():
        try:
            subprocess.Popen(["powercfg.cpl"])
        except Exception:
            pass

    @staticmethod
    def open_user_accounts():
        try:
            subprocess.Popen(["netplwiz"])
        except Exception:
            pass

    @staticmethod
    def open_environment_variables():
        try:
            subprocess.Popen(["SystemPropertiesAdvanced"])
        except Exception:
            pass

    @staticmethod
    def check_network_connections() -> dict:
        try:
            output = subprocess.run(["netstat", "-an"], capture_output=True, text=True, timeout=15)
            lines = output.stdout.split("\n")
            established = [l for l in lines if "ESTABLISHED" in l]
            return {"success": True, "output": f"Active connections: {len(established)}", "details": established[:10]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def get_wifi_networks() -> dict:
        try:
            output = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, timeout=20
            )
            return {"success": True, "output": output.stdout.strip()[:1000]}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def backup_registry() -> dict:
        try:
            backup_path = os.path.join(os.environ.get("USERPROFILE", ""), "registry_backup.reg")
            subprocess.run(["reg", "export", "HKLM\\SYSTEM", backup_path, "/y"], capture_output=True, text=True, timeout=30)
            return {"success": True, "output": f"Registry backed up to: {backup_path}"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def clear_windows_update_cache() -> dict:
        try:
            subprocess.run(["net", "stop", "wuauserv"], capture_output=True, text=True, timeout=10)
            import shutil
            cache_path = r"C:\Windows\SoftwareDistribution\Download"
            if os.path.exists(cache_path):
                for f in os.listdir(cache_path):
                    shutil.rmtree(os.path.join(cache_path, f), ignore_errors=True)
            subprocess.run(["net", "start", "wuauserv"], capture_output=True, text=True, timeout=10)
            return {"success": True, "output": "Windows Update cache cleared"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    @staticmethod
    def repair_windows() -> dict:
        try:
            subprocess.Popen(["ms-settings:recovery"])
            return {"success": True, "output": "Windows Recovery options opened"}
        except Exception as e:
            return {"success": False, "output": str(e)}


# ─── AutoFix Utilities ─────────────────────────────────────────────────────────

class AutoFixTools:
    @staticmethod
    def fix_all_common_issues() -> dict:
        results = []

        try:
            result = SystemTools.clean_temp_files()
            results.append(f"Temp files: Cleaned {result.get('freed_mb', 0)}MB")
        except:
            pass

        try:
            result = SystemTools.clear_recycle_bin()
            results.append("Recycle Bin: Cleared")
        except:
            pass

        try:
            result = SystemTools.clear_dns_cache()
            results.append("DNS Cache: Flushed")
        except:
            pass

        try:
            subprocess.run(["net", "start", "wuauserv"], capture_output=True, text=True, timeout=10)
            results.append("Windows Update: Service started")
        except:
            pass

        return {"success": True, "output": " | ".join(results)}

    @staticmethod
    def optimize_performance() -> dict:
        results = []

        try:
            subprocess.run(["powercfg", "/change", "monitor-timeout-ac", "30"], capture_output=True, text=True, timeout=10)
            results.append("Monitor timeout: Set to 30 min")
        except:
            pass

        try:
            subprocess.run(["powercfg", "/change", "disk-timeout-ac", "0"], capture_output=True, text=True, timeout=10)
            results.append("Disk timeout: Disabled")
        except:
            pass

        try:
            result = SystemTools.clear_font_cache()
            results.append("Font cache: Cleared")
        except:
            pass

        return {"success": True, "output": " | ".join(results)}

    @staticmethod
    def fix_network() -> dict:
        return SystemTools.reset_network()

    @staticmethod
    def fix_services() -> dict:
        services_to_fix = ["wuauserv", "BITS", "Dnscache", "Dhcp"]
        results = []
        for svc in services_to_fix:
            try:
                subprocess.run(["net", "start", svc], capture_output=True, text=True, timeout=10)
                results.append(f"{svc}: Started")
            except:
                results.append(f"{svc}: Failed")
        return {"success": True, "output": " | ".join(results)}


# ─── Benchmark Scanner ──────────────────────────────────────────────────────────

class BenchmarkScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="System Benchmark")
        try:
            import time

            cpu_score = self._cpu_benchmark()
            mem_score = self._memory_benchmark()
            disk_score = self._disk_benchmark()

            result.data = {
                "cpu_score": cpu_score,
                "memory_score": mem_score,
                "disk_score": disk_score,
                "overall_score": round((cpu_score + mem_score + disk_score) / 3, 1),
            }

            if result.data["overall_score"] < 30:
                result.issues.append(Issue(
                    "Benchmark", "warning", "Low System Performance",
                    f"Overall score: {result.data['overall_score']}/100",
                    "Consider upgrading RAM or using SSD."
                ))
                result.health_score -= 15

        except Exception as e:
            result.issues.append(Issue("Benchmark", "warning", "Scan Error", str(e), ""))
        return result

    def _cpu_benchmark(self) -> float:
        try:
            start = time.time()
            total = 0
            for i in range(1000000):
                total += i * i
            end = time.time()
            score = max(0, 100 - (end - start) * 10)
            return round(score, 1)
        except:
            return 50.0

    def _memory_benchmark(self) -> float:
        try:
            import time
            start = time.time()
            data = bytearray(10 * 1024 * 1024)
            for i in range(len(data)):
                data[i] = i % 256
            end = time.time()
            score = max(0, 100 - (end - start) * 20)
            return round(score, 1)
        except:
            return 50.0

    def _disk_benchmark(self) -> float:
        try:
            import time
            test_file = os.path.join(os.environ.get("TEMP", ""), "bench_test.dat")
            start = time.time()
            with open(test_file, "wb") as f:
                f.write(b"0" * (10 * 1024 * 1024))
            end = time.time()
            if os.path.exists(test_file):
                os.remove(test_file)
            score = max(0, 100 - (end - start) * 10)
            return round(score, 1)
        except:
            return 50.0


# ─── Disk Usage Analyzer ─────────────────────────────────────────────────────────

class DiskUsageScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Disk Usage Analysis")
        try:
            drives = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    largest_files = self._find_large_files(part.mountpoint)
                    drives.append({
                        "drive": part.mountpoint,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent,
                        "largest_files": largest_files,
                    })
                except:
                    continue

            result.data = {
                "drives": drives,
            }

            for d in drives:
                if d["percent"] > 90:
                    result.issues.append(Issue(
                        "Disk Usage", "critical", f"Drive {d['drive']} Nearly Full",
                        f"Only {d['free_gb']}GB free ({d['percent']}% used)",
                        "Delete large files or uninstall programs."
                    ))
                    result.health_score -= 20

        except Exception as e:
            result.issues.append(Issue("Disk Usage", "warning", "Scan Error", str(e), ""))
        return result

    def _find_large_files(self, path: str, limit_mb: int = 100) -> list:
        large_files = []
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        size = os.path.getsize(fp)
                        if size > limit_mb * 1024 * 1024:
                            large_files.append({
                                "file": f[:50],
                                "size_mb": round(size / (1024**2), 1),
                                "path": dirpath[:60],
                            })
                    except:
                        continue
                if len(large_files) >= 10:
                    break
        except:
            pass
        return sorted(large_files, key=lambda x: x["size_mb"], reverse=True)[:5]


# ─── Browser Diagnostics ─────────────────────────────────────────────────────────

class BrowserDiagnosticsScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Browser Diagnostics")
        try:
            browsers = {}

            local = os.environ.get("LOCALAPPDATA", "")

            chrome_path = os.path.join(local, r"Google\Chrome\User Data\Default")
            if os.path.exists(chrome_path):
                cache_size = self._get_folder_size(os.path.join(chrome_path, "Cache"))
                cookies = self._get_cookies_count(os.path.join(chrome_path, "Network", "Cookies"))
                browsers["Chrome"] = {"cache_mb": cache_size, "cookies": cookies}

            edge_path = os.path.join(local, r"Microsoft\Edge\User Data\Default")
            if os.path.exists(edge_path):
                cache_size = self._get_folder_size(os.path.join(edge_path, "Cache"))
                cookies = self._get_cookies_count(os.path.join(edge_path, "Network", "Cookies"))
                browsers["Edge"] = {"cache_mb": cache_size, "cookies": cookies}

            firefox_path = os.path.join(local, r"Mozilla\Firefox\Profiles")
            if os.path.exists(firefox_path):
                try:
                    for p in os.listdir(firefox_path):
                        if ".default" in p:
                            cache_size = self._get_folder_size(os.path.join(firefox_path, p, "cache2"))
                            browsers["Firefox"] = {"cache_mb": cache_size, "cookies": "N/A"}
                            break
                except:
                    pass

            result.data = {
                "browsers": browsers,
            }

            for name, data in browsers.items():
                if data.get("cache_mb", 0) > 500:
                    result.issues.append(Issue(
                        "Browser", "warning", f"{name} Cache Large",
                        f"{name} has {data['cache_mb']}MB cached data.",
                        f"Clear {name} cache in settings or use the cleanup tool."
                    ))
                    result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Browser", "warning", "Scan Error", str(e), ""))
        return result

    def _get_folder_size(self, path: str) -> float:
        try:
            if not os.path.exists(path):
                return 0
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except:
                        continue
            return round(total / (1024**2), 1)
        except:
            return 0

    def _get_cookies_count(self, path: str) -> int:
        try:
            if os.path.exists(path):
                return int(os.path.getsize(path) / 100)
            return 0
        except:
            return 0


# ─── Windows Reliability Monitor Scanner ─────────────────────────────────────────

class ReliabilityScanner:
    """Reads Windows Reliability Monitor data — the built-in stability tracker."""

    def scan(self) -> ScanResult:
        result = ScanResult(category="Windows Reliability")
        try:
            records = self._get_reliability_records()
            stability = self._get_stability_index()
            problem_reports = self._get_problem_reports()

            result.data = {
                "stability_index": stability,
                "failure_records": records[:30],
                "total_failures_30d": len(records),
                "problem_reports": problem_reports[:20],
                "total_problem_reports": len(problem_reports),
            }

            hw_failures = [r for r in records if r.get("type") == "Hardware"]
            sw_failures = [r for r in records if r.get("type") in ("Application", "Windows")]
            misc_failures = [r for r in records if r.get("type") == "MiscellaneousFailure"]

            if stability is not None and stability < 3:
                result.issues.append(Issue(
                    "Windows Reliability", "critical", f"System Stability Very Low ({stability:.1f}/10)",
                    f"Windows Reliability Index is {stability:.1f} out of 10. Your system is highly unstable with frequent crashes and failures.",
                    "Run 'sfc /scannow' and 'DISM /Online /Cleanup-Image /RestoreHealth' as admin. Update all drivers. Consider a clean Windows install if problems persist."
                ))
                result.health_score -= 35
            elif stability is not None and stability < 6:
                result.issues.append(Issue(
                    "Windows Reliability", "warning", f"System Stability Below Average ({stability:.1f}/10)",
                    f"Windows rates your system stability at {stability:.1f}/10. Crashes and errors are occurring more than normal.",
                    "Check Reliability Monitor (perfmon /rel) for details. Update drivers and problematic software."
                ))
                result.health_score -= 20
            elif stability is not None and stability < 8:
                result.issues.append(Issue(
                    "Windows Reliability", "info", f"System Stability Fair ({stability:.1f}/10)",
                    f"Stability index is {stability:.1f}/10. Some issues have occurred recently.",
                    "Open Reliability Monitor (perfmon /rel) to review recent problems."
                ))
                result.health_score -= 5

            if hw_failures:
                hw_sources = list(set(r.get("source", "Unknown") for r in hw_failures[:10]))
                result.issues.append(Issue(
                    "Windows Reliability", "critical", f"{len(hw_failures)} Hardware Failure(s) Detected",
                    f"Windows detected hardware failures from: {', '.join(hw_sources[:4])}. "
                    f"Latest: {hw_failures[0].get('message', 'Unknown')[:150]}",
                    "Check Device Manager for yellow exclamation marks. Update or reinstall drivers. Hardware may need replacement."
                ))
                result.health_score -= 20

            if len(sw_failures) > 5:
                sw_sources = list(set(r.get("source", "Unknown") for r in sw_failures[:10]))
                result.issues.append(Issue(
                    "Windows Reliability", "warning", f"{len(sw_failures)} Software Failures (Last 30 Days)",
                    f"Applications crashing: {', '.join(sw_sources[:5])}.",
                    "Update or reinstall these applications. If Windows components are crashing, run 'sfc /scannow'."
                ))
                result.health_score -= 12
            elif sw_failures:
                result.issues.append(Issue(
                    "Windows Reliability", "info", f"{len(sw_failures)} Software Failure(s) Recorded",
                    f"Recent software issues from: {', '.join(set(r.get('source', '') for r in sw_failures[:5]))}.",
                    "Monitor for recurring crashes. Update software if needed."
                ))
                result.health_score -= 3

            if misc_failures:
                result.issues.append(Issue(
                    "Windows Reliability", "warning", f"{len(misc_failures)} Miscellaneous System Failures",
                    f"Windows recorded {len(misc_failures)} unexpected failures including unexpected shutdowns or hangs.",
                    "Check power supply, RAM stability, and disk health. Run Windows Memory Diagnostic."
                ))
                result.health_score -= 10

            if len(problem_reports) > 10:
                apps = list(set(r.get("app", "Unknown") for r in problem_reports))
                result.issues.append(Issue(
                    "Windows Reliability", "warning", f"{len(problem_reports)} Problem Reports Stored",
                    f"Windows has stored crash/error reports for: {', '.join(apps[:5])}{'...' if len(apps) > 5 else ''}.",
                    "These reports can be reviewed in Settings > Privacy > Diagnostics & Feedback, or Control Panel > Problem Reports."
                ))
                result.health_score -= 8

        except Exception as e:
            result.issues.append(Issue("Windows Reliability", "info", "Reliability Scan Limited", str(e), ""))
        return result

    def _get_reliability_records(self) -> list:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-CimInstance -ClassName Win32_ReliabilityRecords -ErrorAction SilentlyContinue | '
                 'Where-Object {$_.TimeGenerated -gt (Get-Date).AddDays(-30)} | '
                 'Select-Object -First 50 ProductName,SourceName,EventIdentifier,Message,TimeGenerated,@{N="Type";E={$_.RecordType}} | '
                 'ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=30
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                return [
                    {
                        "source": r.get("SourceName") or r.get("ProductName", "Unknown"),
                        "message": str(r.get("Message", ""))[:300],
                        "time": str(r.get("TimeGenerated", "")),
                        "type": str(r.get("Type", "")),
                        "event_id": r.get("EventIdentifier"),
                    }
                    for r in data if r.get("Message")
                ]
        except Exception:
            pass
        return []

    def _get_stability_index(self) -> Optional[float]:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-CimInstance -ClassName Win32_ReliabilityStabilityMetrics -ErrorAction SilentlyContinue | '
                 'Sort-Object -Property TimeGenerated -Descending | '
                 'Select-Object -First 1 -ExpandProperty SystemStabilityIndex'],
                capture_output=True, text=True, timeout=15
            )
            if output.returncode == 0 and output.stdout.strip():
                val = output.stdout.strip()
                return float(val)
        except Exception:
            pass
        return None

    def _get_problem_reports(self) -> list:
        reports = []
        wer_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WER", "ReportArchive")
        if os.path.exists(wer_path):
            try:
                cutoff = time.time() - 30 * 86400
                for folder in os.listdir(wer_path):
                    fp = os.path.join(wer_path, folder)
                    if os.path.isdir(fp):
                        try:
                            mtime = os.path.getmtime(fp)
                            if mtime > cutoff:
                                report_file = os.path.join(fp, "Report.wer")
                                app_name = folder
                                if os.path.exists(report_file):
                                    try:
                                        with open(report_file, "r", errors="ignore") as f:
                                            for line in f:
                                                if line.startswith("AppName="):
                                                    app_name = line.split("=", 1)[1].strip()
                                                    break
                                    except Exception:
                                        pass
                                reports.append({
                                    "app": app_name,
                                    "folder": folder,
                                    "time": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                                })
                        except OSError:
                            continue
            except Exception:
                pass
        return reports


# ─── Windows Update Scanner ──────────────────────────────────────────────────────

class WindowsUpdateScanner:
    """Checks Windows Update history for failed updates and pending issues."""

    def scan(self) -> ScanResult:
        result = ScanResult(category="Windows Update")
        try:
            updates = self._get_update_history()
            failed = [u for u in updates if u.get("status") == "Failed"]
            succeeded = [u for u in updates if u.get("status") == "Succeeded"]
            pending = self._check_pending_updates()

            result.data = {
                "recent_updates": updates[:20],
                "failed_updates": failed[:10],
                "failed_count": len(failed),
                "succeeded_count": len(succeeded),
                "total_recent": len(updates),
                "pending_count": pending,
            }

            if len(failed) > 3:
                names = [u.get("title", "Unknown")[:60] for u in failed[:3]]
                result.issues.append(Issue(
                    "Windows Update", "critical", f"{len(failed)} Windows Updates Failed",
                    f"Multiple Windows updates failed to install. Failed: {'; '.join(names)}. "
                    f"Your system is missing security patches and may be vulnerable.",
                    "1) Run Windows Update troubleshooter (Settings > Update > Troubleshoot) "
                    "2) Run 'DISM /Online /Cleanup-Image /RestoreHealth' as admin "
                    "3) Then 'sfc /scannow' 4) Retry updates."
                ))
                result.health_score -= 25
            elif len(failed) > 0:
                result.issues.append(Issue(
                    "Windows Update", "warning", f"{len(failed)} Failed Update(s)",
                    f"Some Windows updates failed: {failed[0].get('title', 'Unknown')[:80]}.",
                    "Try running Windows Update again. If it persists, run Windows Update Troubleshooter."
                ))
                result.health_score -= 12

            if pending and pending > 5:
                result.issues.append(Issue(
                    "Windows Update", "warning", f"{pending} Pending Updates",
                    f"There are {pending} updates waiting to be installed including possible security patches.",
                    "Go to Settings > Windows Update and install all pending updates. Restart when prompted."
                ))
                result.health_score -= 10

            if not updates:
                result.issues.append(Issue(
                    "Windows Update", "warning", "Cannot Read Update History",
                    "Unable to retrieve Windows Update history. Updates may not be running properly.",
                    "Open Settings > Windows Update and check for updates manually."
                ))
                result.health_score -= 10

        except Exception as e:
            result.issues.append(Issue("Windows Update", "info", "Update Scan Limited", str(e), ""))
        return result

    def _get_update_history(self) -> list:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-HotFix -ErrorAction SilentlyContinue | '
                 'Sort-Object -Property InstalledOn -Descending -ErrorAction SilentlyContinue | '
                 'Select-Object -First 20 Description,HotFixID,InstalledOn | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=20
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                return [{"title": f"{u.get('Description', '')} ({u.get('HotFixID', '')})",
                         "date": str(u.get("InstalledOn", "")), "status": "Succeeded"} for u in data]
        except Exception:
            pass

        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 '$Session = New-Object -ComObject Microsoft.Update.Session; '
                 '$Searcher = $Session.CreateUpdateSearcher(); '
                 '$History = $Searcher.QueryHistory(0, 30); '
                 '$History | Select-Object Title,Date,@{N="Status";E={switch($_.ResultCode){0{"NotStarted"}1{"InProgress"}2{"Succeeded"}3{"SucceededWithErrors"}4{"Failed"}5{"Aborted"}}}} | '
                 'ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=25
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                return [{"title": u.get("Title", "Unknown"), "date": str(u.get("Date", "")),
                         "status": u.get("Status", "Unknown")} for u in data]
        except Exception:
            pass
        return []

    def _check_pending_updates(self) -> int:
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 '$UpdateSession = New-Object -ComObject Microsoft.Update.Session; '
                 '$Searcher = $UpdateSession.CreateUpdateSearcher(); '
                 '$Results = $Searcher.Search("IsInstalled=0"); '
                 '$Results.Updates.Count'],
                capture_output=True, text=True, timeout=30
            )
            if output.returncode == 0 and output.stdout.strip():
                return int(output.stdout.strip())
        except Exception:
            pass
        return 0


# ─── Windows System Health Scanner ───────────────────────────────────────────────

class SystemHealthScanner:
    """Checks Windows system file integrity, DISM health, and Action Center alerts."""

    def scan(self) -> ScanResult:
        result = ScanResult(category="System Health")
        try:
            sfc_status = self._check_sfc_log()
            dism_status = self._check_component_store()
            action_center = self._get_action_center_issues()
            perf_issues = self._check_performance_issues()

            result.data = {
                "sfc_status": sfc_status,
                "component_store": dism_status,
                "action_center_items": action_center,
                "performance_issues": perf_issues,
            }

            if sfc_status.get("corrupted"):
                result.issues.append(Issue(
                    "System Health", "critical", "Corrupted System Files Detected",
                    f"Windows System File Checker found corrupted files. {sfc_status.get('detail', '')}",
                    "Run as Administrator: 1) 'DISM /Online /Cleanup-Image /RestoreHealth' 2) Then 'sfc /scannow' 3) Restart PC."
                ))
                result.health_score -= 25
            elif sfc_status.get("repaired"):
                result.issues.append(Issue(
                    "System Health", "warning", "System Files Were Repaired",
                    "Windows previously found and repaired corrupted system files.",
                    "Run 'sfc /scannow' again to verify all files are now intact."
                ))
                result.health_score -= 8

            if dism_status.get("repairable"):
                result.issues.append(Issue(
                    "System Health", "warning", "Windows Component Store Needs Repair",
                    "The Windows component store has corruption that can be repaired.",
                    "Run as Admin: 'DISM /Online /Cleanup-Image /RestoreHealth' then restart."
                ))
                result.health_score -= 15

            for item in action_center:
                sev = "critical" if item.get("severity") == "critical" else "warning"
                result.issues.append(Issue(
                    "System Health", sev, f"Windows Alert: {item.get('title', 'Unknown')}",
                    item.get("description", "Windows has flagged a system issue."),
                    item.get("action", "Check Windows Security / Action Center for details.")
                ))
                result.health_score -= 15 if sev == "critical" else 8

            for pi in perf_issues:
                result.issues.append(Issue(
                    "System Health", "warning", pi.get("title", "Performance Issue"),
                    pi.get("description", ""),
                    pi.get("fix", "")
                ))
                result.health_score -= 8

        except Exception as e:
            result.issues.append(Issue("System Health", "info", "Health Scan Limited", str(e), ""))
        return result

    def _check_sfc_log(self) -> dict:
        result = {"corrupted": False, "repaired": False, "detail": ""}
        log_path = r"C:\Windows\Logs\CBS\CBS.log"
        try:
            if os.path.exists(log_path):
                size = os.path.getsize(log_path)
                read_bytes = min(size, 500000)
                with open(log_path, "r", errors="ignore") as f:
                    if size > read_bytes:
                        f.seek(size - read_bytes)
                    content = f.read()
                if "Cannot repair member file" in content or "corrupt" in content.lower():
                    corrupt_count = content.lower().count("cannot repair")
                    result["corrupted"] = True
                    result["detail"] = f"Found {corrupt_count} unrepairable file references in CBS log."
                elif "repaired" in content.lower() or "Repair complete" in content:
                    result["repaired"] = True
                    result["detail"] = "System files were previously repaired."
        except Exception:
            pass
        return result

    def _check_component_store(self) -> dict:
        result = {"healthy": True, "repairable": False}
        try:
            output = subprocess.run(
                ["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"],
                capture_output=True, text=True, timeout=60
            )
            stdout = output.stdout.lower()
            if "repairable" in stdout:
                result["healthy"] = False
                result["repairable"] = True
            elif "no component store corruption" not in stdout and "healthy" not in stdout:
                if output.returncode != 0:
                    result["healthy"] = False
        except Exception:
            pass
        return result

    def _get_action_center_issues(self) -> list:
        issues = []
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction SilentlyContinue | '
                 'Select-Object displayName,productState | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=15
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for av in data:
                    state = av.get("productState", 0)
                    # Bits 12-16: product state. 0x1000 = on, 0x0000 = off
                    if isinstance(state, int) and not (state >> 12 & 0x1):
                        issues.append({
                            "title": f"Antivirus Off: {av.get('displayName', 'Unknown')}",
                            "description": f"{av.get('displayName', 'Unknown')} is installed but not actively protecting.",
                            "action": "Enable your antivirus or switch to Windows Defender.",
                            "severity": "critical",
                        })
        except Exception:
            pass

        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-CimInstance -Namespace root/SecurityCenter2 -ClassName FirewallProduct -ErrorAction SilentlyContinue | '
                 'Select-Object displayName,productState | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=15
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for fw in data:
                    state = fw.get("productState", 0)
                    if isinstance(state, int) and not (state >> 12 & 0x1):
                        issues.append({
                            "title": f"Firewall Off: {fw.get('displayName', 'Unknown')}",
                            "description": f"Firewall '{fw.get('displayName', '')}' is not active.",
                            "action": "Enable your firewall for network protection.",
                            "severity": "critical",
                        })
        except Exception:
            pass
        return issues

    def _check_performance_issues(self) -> list:
        issues = []
        try:
            # Check if page file is too small
            output = subprocess.run(
                ["powershell", "-Command",
                 'Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue | '
                 'Select-Object AllocatedBaseSize,CurrentUsage,PeakUsage | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=10
            )
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for pf in data:
                    alloc = pf.get("AllocatedBaseSize", 0)
                    peak = pf.get("PeakUsage", 0)
                    if alloc > 0 and peak > alloc * 0.8:
                        issues.append({
                            "title": "Page File Nearly Full",
                            "description": f"Page file peak usage ({peak}MB) is close to allocated size ({alloc}MB). System may run out of virtual memory.",
                            "fix": "Increase page file size: System Properties > Advanced > Performance > Virtual Memory."
                        })
        except Exception:
            pass

        try:
            # Check power plan
            output = subprocess.run(
                ["powershell", "-Command",
                 'powercfg /getactivescheme'],
                capture_output=True, text=True, timeout=10
            )
            if output.returncode == 0:
                out = output.stdout.lower()
                if "power saver" in out:
                    issues.append({
                        "title": "Power Saver Mode Active",
                        "description": "PC is running in Power Saver mode which reduces CPU speed and overall performance.",
                        "fix": "Switch to 'Balanced' or 'High Performance': Control Panel > Power Options."
                    })
        except Exception:
            pass
        return issues


# ─── USB Devices Scanner ──────────────────────────────────────────────────────

class USBDevicesScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="USB Devices")
        try:
            devices = []
            if WMI_AVAILABLE:
                w = wmi.WMI()
                for usb in w.Win32_USBControllerDevice():
                    try:
                        dev = usb.Dependent
                        if dev:
                            devices.append({
                                "device": dev.Name if hasattr(dev, "Name") else "Unknown",
                                "device_id": dev.DeviceID if hasattr(dev, "DeviceID") else "",
                            })
                    except Exception:
                        continue

            result.data = {
                "total_usb_devices": len(devices),
                "devices": devices[:30],
            }

            if len(devices) > 20:
                result.issues.append(Issue(
                    "USB", "info", "Many USB Devices Connected",
                    f"{len(devices)} USB devices detected.",
                    "Too many USB devices can cause power issues. Disconnect unused devices."
                ))
                result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("USB", "warning", "Scan Error", str(e), ""))
        return result


# ─── Printer Scanner ───────────────────────────────────────────────────────────

class PrinterScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Printers")
        try:
            printers = []
            if WMI_AVAILABLE:
                w = wmi.WMI()
                for prt in w.Win32_Printer():
                    printers.append({
                        "name": prt.Name,
                        "status": prt.Status,
                        "default": prt.Default,
                        "driver": prt.DriverName,
                        "port": prt.PortName,
                    })

            result.data = {
                "total_printers": len(printers),
                "printers": printers,
            }

            offline = [p for p in printers if p.get("status") != "OK"]
            if offline:
                result.issues.append(Issue(
                    "Printers", "warning", f"{len(offline)} Printer(s) Offline",
                    f"Printers offline: {', '.join(p['name'] for p in offline[:2])}",
                    "Check printer connections and power. Remove stuck print jobs."
                ))
                result.health_score -= 5

        except Exception as e:
            result.issues.append(Issue("Printers", "warning", "Scan Error", str(e), ""))
        return result


# ─── Scheduled Tasks Scanner ─────────────────────────────────────────────────

class ScheduledTasksScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Scheduled Tasks")
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} | "
                 "Select-Object TaskName,State,TaskPath | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=30
            )

            tasks = []
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for t in data:
                    tasks.append({
                        "name": t.get("TaskName", "Unknown"),
                        "path": t.get("TaskPath", ""),
                        "state": t.get("State", "Unknown"),
                    })

            result.data = {
                "total_tasks": len(tasks),
                "tasks": tasks[:50],
            }

            critical_tasks = [t for t in tasks if any(k in t.get("name", "").lower() for k in ("update", "defender", "backup"))]
            if len(critical_tasks) > 10:
                result.issues.append(Issue(
                    "Scheduled Tasks", "info", "Many Scheduled Tasks",
                    f"{len(tasks)} active scheduled tasks found.",
                    "Review tasks in Task Scheduler to disable unnecessary ones."
                ))
                result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("Scheduled Tasks", "warning", "Scan Error", str(e), ""))
        return result


# ─── Firewall Rules Scanner ──────────────────────────────────────────────────

class FirewallScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Firewall Rules")
        try:
            inbound = []
            outbound = []

            for direction, rules, name in [("Inbound", inbound, "inbound"), ("Outbound", outbound, "outbound")]:
                output = subprocess.run(
                    ["powershell", "-Command",
                     f"Get-NetFirewallRule -Direction {direction} -Enabled True | "
                     f"Select-Object Name,DisplayName,Profile,Action | ConvertTo-Json -Compress"],
                    capture_output=True, text=True, timeout=20
                )
                if output.returncode == 0 and output.stdout.strip():
                    import json
                    data = json.loads(output.stdout)
                    if isinstance(data, dict):
                        data = [data]
                    for r in data[:30]:
                        rules.append({
                            "name": r.get("DisplayName", r.get("Name", "")),
                            "action": r.get("Action", ""),
                            "profile": str(r.get("Profile", "")),
                        })

            result.data = {
                "inbound_rules": len(inbound),
                "outbound_rules": len(outbound),
                "inbound": inbound[:20],
                "outbound": outbound[:20],
            }

        except Exception as e:
            result.issues.append(Issue("Firewall", "warning", "Scan Error", str(e), ""))
        return result


# ─── DNS Settings Scanner ───────────────────────────────────────────────────

class DNSResolverScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="DNS Resolver")
        try:
            dns_servers = []
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {$_.ServerAddresses} | "
                 "Select-Object InterfaceAlias,ServerAddresses | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=15
            )

            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for d in data:
                    dns_servers.append({
                        "adapter": d.get("InterfaceAlias", "Unknown"),
                        "servers": d.get("ServerAddresses", []),
                    })

            result.data = {
                "dns_configurations": dns_servers,
            }

            custom_dns = [d for d in dns_servers if d.get("servers") and not any(s in d["servers"] for s in ["127.0.0.1", ""])]
            if custom_dns:
                result.issues.append(Issue(
                    "DNS", "info", "Custom DNS Servers Configured",
                    f"Custom DNS on {len(custom_dns)} adapter(s).",
                    "Using custom DNS can improve speed or privacy. Verify your provider is trustworthy."
                ))
                result.health_score -= 1

        except Exception as e:
            result.issues.append(Issue("DNS", "warning", "Scan Error", str(e), ""))
        return result


# ─── Hosts File Scanner ─────────────────────────────────────────────────────

class HostsFileScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Hosts File")
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            entries = []

            if os.path.exists(hosts_path):
                with open(hosts_path, "r", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("::"):
                            parts = line.split()
                            if len(parts) >= 2:
                                entries.append({
                                    "ip": parts[0],
                                    "hostname": parts[1],
                                })

            result.data = {
                "total_entries": len(entries),
                "entries": entries[:30],
            }

            suspicious = [e for e in entries if any(s in e.get("hostname", "").lower() for s in ["localhost", "local"])]
            if len(entries) > 20 and not suspicious:
                result.issues.append(Issue(
                    "Hosts", "info", "Many Hosts Entries",
                    f"{len(entries)} custom entries in hosts file.",
                    "Review hosts file for unwanted redirections."
                ))
                result.health_score -= 1

        except Exception as e:
            result.issues.append(Issue("Hosts", "warning", "Scan Error", str(e), ""))
        return result


# ─── Network Shares Scanner ─────────────────────────────────────────────────

class NetworkSharesScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Network Shares")
        try:
            shares = []
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-SmbShare | Select-Object Name,Path,Description,ShareType | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=15
            )

            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for s in data:
                    shares.append({
                        "name": s.get("Name", ""),
                        "path": s.get("Path", ""),
                        "type": str(s.get("ShareType", "")),
                        "description": s.get("Description", ""),
                    })

            result.data = {
                "total_shares": len(shares),
                "shares": shares,
            }

            if len(shares) > 10:
                result.issues.append(Issue(
                    "Network Shares", "info", "Many Shared Folders",
                    f"{len(shares)} network shares configured.",
                    "Review shares in Computer Management to remove unnecessary ones."
                ))
                result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("Network Shares", "warning", "Scan Error", str(e), ""))
        return result


# ─── Registry Health Scanner ──────────────────────────────────────────────────

class RegistryScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Registry Health")
        try:
            keys_to_check = {
                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run": "Startup Programs",
                "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run": "User Startup",
                "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters": "Network TCP/IP",
            }

            results = {}
            for key_path, desc in keys_to_check.items():
                try:
                    parts = key_path.split("\\", 2)
                    hive = getattr(winreg, parts[0])
                    key = winreg.OpenKey(hive, parts[2])
                    i = 0
                    values = []
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            values.append({"name": name, "value": str(value)[:100]})
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                    results[desc] = {"count": len(values), "values": values[:10]}
                except Exception as e:
                    results[desc] = {"error": str(e)}

            result.data = {
                "registry_keys": results,
            }

            for desc, data in results.items():
                if data.get("count", 0) > 20:
                    result.issues.append(Issue(
                        "Registry", "warning", f"Many Entries in {desc}",
                        f"{data.get('count', 0)} registry values found.",
                        "Too many startup entries can slow boot time."
                    ))
                    result.health_score -= 3

        except Exception as e:
            result.issues.append(Issue("Registry", "warning", "Scan Error", str(e), ""))
        return result


# ─── Windows Features Scanner ────────────────────────────────────────────────

class WindowsFeaturesScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Windows Features")
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-WindowsOptionalFeature -Online | Where-Object {$_.State -eq 'Enabled'} | "
                 "Select-Object FeatureName,State | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=30
            )

            features = []
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for f in data:
                    features.append({
                        "name": f.get("FeatureName", "Unknown"),
                        "state": f.get("State", ""),
                    })

            result.data = {
                "enabled_features": features,
                "total_enabled": len(features),
            }

            if len(features) > 20:
                result.issues.append(Issue(
                    "Windows Features", "info", "Many Windows Features Enabled",
                    f"{len(features)} features enabled.",
                    "Disabling unused features can improve performance."
                ))
                result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("Windows Features", "warning", "Scan Error", str(e), ""))
        return result


# ─── Environment Variables Scanner ───────────────────────────────────────────

class EnvironmentVarsScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Environment Variables")
        try:
            user_vars = os.environ
            system_vars = {}

            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        system_vars[name] = str(value)[:100]
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                pass

            result.data = {
                "user_vars_count": len([k for k in user_vars.keys() if not k.startswith("_")]),
                "system_vars_count": len(system_vars),
                "path_entries": os.environ.get("PATH", "").count(";") + 1,
            }

            path = os.environ.get("PATH", "")
            if path.count(";") > 20:
                result.issues.append(Issue(
                    "Environment", "info", "Many PATH Entries",
                    f"PATH has {path.count(';') + 1} entries.",
                    "Too many PATH entries can cause conflicts."
                ))
                result.health_score -= 2

        except Exception as e:
            result.issues.append(Issue("Environment", "warning", "Scan Error", str(e), ""))
        return result


# ─── IP Configuration Scanner ────────────────────────────────────────────────

class IPConfigScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="IP Configuration")
        try:
            output = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=15)

            adapters = []
            current = {}
            for line in output.stdout.split("\n"):
                line = line.strip()
                if line.endswith(":"):
                    if current:
                        adapters.append(current)
                    current = {"name": line.rstrip(":").strip(), "details": []}
                elif line:
                    current.setdefault("details", []).append(line)

            if current:
                adapters.append(current)

            result.data = {
                "adapters": adapters[:10],
                "total_adapters": len(adapters),
            }

            ipv6_enabled = any("IPv6" in str(a) for a in adapters)
            if ipv6_enabled:
                result.issues.append(Issue(
                    "Network", "info", "IPv6 Enabled",
                    "IPv6 is enabled on your system.",
                    "IPv6 is fine but can be disabled if not needed."
                ))
                result.health_score -= 1

        except Exception as e:
            result.issues.append(Issue("IP Config", "warning", "Scan Error", str(e), ""))
        return result


# ─── Quick Error Summary Scanner ────────────────────────────────────────────

class QuickErrorsScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Error Summary")
        try:
            output = subprocess.run(
                ["powershell", "-Command",
                 "Get-WinEvent -LogName System -MaxEvents 50 | "
                 "Where-Object {$_.LevelDisplayName -in @('Error','Critical')} | "
                 "Select-Object TimeCreated,ProviderName,Message | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=30
            )

            errors = []
            if output.returncode == 0 and output.stdout.strip():
                import json
                data = json.loads(output.stdout)
                if isinstance(data, dict):
                    data = [data]
                for e in data:
                    errors.append({
                        "time": str(e.get("TimeCreated", ""))[:19],
                        "source": e.get("ProviderName", "Unknown"),
                        "message": str(e.get("Message", ""))[:150],
                    })

            result.data = {
                "recent_errors": errors,
                "error_count": len(errors),
            }

            if len(errors) > 15:
                result.issues.append(Issue(
                    "Error Summary", "warning", "Many Recent Errors",
                    f"{len(errors)} errors found in System log.",
                    "Review Event Viewer for patterns."
                ))
                result.health_score -= 10

        except Exception as e:
            result.issues.append(Issue("Error Summary", "warning", "Scan Error", str(e), ""))
        return result


# ─── WiFi Networks Scanner ─────────────────────────────────────────────────────

class WiFiScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="WiFi Networks")
        try:
            output = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True, timeout=20
            )

            networks = []
            current = {}
            for line in output.stdout.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    if current and current.get("ssid"):
                        networks.append(current)
                    current = {"ssid": line.split(":", 1)[1].strip() if ":" in line else ""}
                elif "Signal" in line and current.get("ssid"):
                    try:
                        current["signal"] = line.split(":")[1].strip()
                    except:
                        pass
                elif "Authentication" in line and current.get("ssid"):
                    try:
                        current["auth"] = line.split(":")[1].strip()
                    except:
                        pass

            if current and current.get("ssid"):
                networks.append(current)

            result.data = {
                "networks": networks[:20],
                "total_found": len(networks),
            }

            if not networks:
                result.issues.append(Issue(
                    "WiFi", "info", "No WiFi Networks Found",
                    "No wireless networks detected (may be using Ethernet).",
                    ""
                ))

        except Exception as e:
            result.issues.append(Issue("WiFi", "warning", "Scan Error", str(e), ""))
        return result


# ─── Startup Performance Scanner ─────────────────────────────────────────────

class StartupPerformanceScanner:
    def scan(self) -> ScanResult:
        result = ScanResult(category="Startup Performance")
        try:
            boot_times = []
            try:
                output = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_BootEnvironment | Select-Object BootLoaderName,LastLaunchTime | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=15
                )
                if output.returncode == 0 and output.stdout.strip():
                    result.data["boot_info"] = output.stdout.strip()[:500]
            except:
                pass

            startup_programs = []
            key_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            ]
            for hive, path in key_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            startup_programs.append({"name": name, "path": value[:80]})
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except:
                    pass

            result.data = {
                "startup_items": startup_programs,
                "total_startup_items": len(startup_programs),
            }

            if len(startup_programs) > 15:
                result.issues.append(Issue(
                    "Startup", "warning", "Many Startup Programs",
                    f"{len(startup_programs)} programs start with Windows.",
                    "Disable unnecessary programs in Task Manager > Startup"
                ))
                result.health_score -= 8

        except Exception as e:
            result.issues.append(Issue("Startup Perf", "warning", "Scan Error", str(e), ""))
        return result


# ─── Master Scanner ─────────────────────────────────────────────────────────────

class MasterScanner:
    """Orchestrates all scanners and collects results."""

    def __init__(self):
        self.scanners = {
            "system": SystemScanner(),
            "cpu": CPUScanner(),
            "memory": MemoryScanner(),
            "disk": DiskScanner(),
            "network": NetworkScanner(),
            "gpu": GPUScanner(),
            "processes": ProcessScanner(),
            "security": SecurityScanner(),
            "battery": BatteryScanner(),
            "startup": StartupScanner(),
            "installed_software": InstalledSoftwareScanner(),
            "drivers": DriversScanner(),
            "services": ServicesScanner(),
            "temp_files": TempFilesScanner(),
            "reliability": ReliabilityScanner(),
            "windows_update": WindowsUpdateScanner(),
            "system_health": SystemHealthScanner(),
            "event_logs": EventLogScanner(),
            "usb_devices": USBDevicesScanner(),
            "printers": PrinterScanner(),
            "scheduled_tasks": ScheduledTasksScanner(),
            "firewall_rules": FirewallScanner(),
            "dns_resolver": DNSResolverScanner(),
            "hosts_file": HostsFileScanner(),
            "network_shares": NetworkSharesScanner(),
            "registry": RegistryScanner(),
            "windows_features": WindowsFeaturesScanner(),
            "environment_vars": EnvironmentVarsScanner(),
            "ip_config": IPConfigScanner(),
            "error_summary": QuickErrorsScanner(),
            "benchmark": BenchmarkScanner(),
            "disk_usage": DiskUsageScanner(),
            "browser_diagnostics": BrowserDiagnosticsScanner(),
            "wifi_networks": WiFiScanner(),
            "startup_performance": StartupPerformanceScanner(),
        }

    def run_all_scans(self, progress_callback=None) -> dict:
        results = {}
        total = len(self.scanners)
        for i, (name, scanner) in enumerate(self.scanners.items()):
            if progress_callback:
                progress_callback(name, i, total)
            results[name] = scanner.scan()
        return results

    def calculate_overall_health(self, results: dict) -> float:
        if not results:
            return 100.0

        weights = {
            "cpu": 3, "memory": 3, "disk": 3, "network": 2, "gpu": 1,
            "security": 3, "processes": 2, "system": 1, "battery": 1,
            "startup": 1, "event_logs": 3, "drivers": 2, "services": 2,
            "installed_software": 0.5, "temp_files": 1,
            "reliability": 4, "windows_update": 3, "system_health": 4,
            "usb_devices": 0.5, "printers": 0.5, "scheduled_tasks": 0.5,
            "firewall_rules": 1, "dns_resolver": 1, "hosts_file": 1,
            "network_shares": 0.5, "registry": 0.5, "windows_features": 0.5,
            "environment_vars": 0.5, "ip_config": 0.5, "error_summary": 2,
            "benchmark": 1, "disk_usage": 1, "browser_diagnostics": 0.5,
            "wifi_networks": 0.5, "startup_performance": 1,
        }

        weighted_sum = 0
        total_weight = 0
        worst_score = 100

        for name, r in results.items():
            w = weights.get(name, 1)
            weighted_sum += r.health_score * w
            total_weight += w
            if r.health_score < worst_score:
                worst_score = r.health_score

        avg = weighted_sum / total_weight if total_weight else 100

        # Pull score toward worst scanner to avoid hiding serious problems
        final = avg * 0.6 + worst_score * 0.4
        return max(0, min(100, final))

    def get_all_issues(self, results: dict) -> list:
        issues = []
        for r in results.values():
            issues.extend(r.issues)
        return issues
