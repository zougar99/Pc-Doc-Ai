"""
PC Doctor - AI-Powered Windows System Diagnostic Tool
Full GUI application with real-time monitoring, system tools, and AI chat.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys
import json
import webbrowser
from datetime import datetime

from scanners import (
    MasterScanner, Issue, RealTimeMonitor, SystemTools,
    InstalledSoftwareScanner, DriversScanner, ServicesScanner, TempFilesScanner,
    ReliabilityScanner, WindowsUpdateScanner, SystemHealthScanner,
)
from ai_engine import AIAnalyzer, InteractiveAI
from report_generator import ReportGenerator

# ─── Theme ───────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":       "#0b0f19",
    "bg2":      "#111827",
    "card":     "#1f2937",
    "card2":    "#374151",
    "border":   "#374151",
    "accent":   "#3b82f6",
    "accent2":  "#2563eb",
    "green":    "#22c55e",
    "yellow":   "#eab308",
    "orange":   "#f97316",
    "red":      "#ef4444",
    "text":     "#f1f5f9",
    "dim":      "#9ca3af",
    "purple":   "#a78bfa",
    "cyan":     "#22d3ee",
    "pink":     "#f472b6",
}


def _hcolor(score):
    if score >= 85: return C["green"]
    if score >= 70: return C["yellow"]
    if score >= 50: return C["orange"]
    return C["red"]

def _hlabel(score):
    if score >= 85: return "EXCELLENT"
    if score >= 70: return "GOOD"
    if score >= 50: return "FAIR"
    if score >= 30: return "POOR"
    return "CRITICAL"

def _scolor(sev):
    return {"critical": C["red"], "warning": C["yellow"], "info": C["accent"]}.get(sev, C["dim"])


# ─── Reusable Widgets ────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """Compact stat card with icon-like label, value and optional bar."""
    def __init__(self, master, title, value, color=None, bar_pct=None, **kw):
        super().__init__(master, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"], **kw)
        color = color or C["text"]
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 11), text_color=C["dim"]).pack(padx=14, pady=(12, 0), anchor="w")
        ctk.CTkLabel(self, text=str(value), font=("Segoe UI", 22, "bold"), text_color=color).pack(padx=14, pady=(0, 2), anchor="w")
        if bar_pct is not None:
            pct = max(0, min(bar_pct / 100, 1.0))
            bc = C["green"] if pct < 0.6 else C["yellow"] if pct < 0.8 else C["red"]
            bar = ctk.CTkProgressBar(self, progress_color=bc, fg_color=C["bg2"], height=8, corner_radius=4, width=140)
            bar.set(pct)
            bar.pack(padx=14, pady=(0, 12), anchor="w")
        else:
            ctk.CTkLabel(self, text="", height=6).pack()


class InfoTable(ctk.CTkFrame):
    """A card with a title and key-value rows."""
    def __init__(self, master, title, rows, accent=C["accent"], **kw):
        super().__init__(master, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"], **kw)
        ctk.CTkLabel(self, text=title, font=("Segoe UI", 15, "bold"), text_color=accent).pack(fill="x", padx=16, pady=(14, 4), anchor="w")
        ctk.CTkFrame(self, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=(0, 6))
        for key, val, clr in rows:
            r = ctk.CTkFrame(self, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(r, text=str(key), font=("Segoe UI", 12), text_color=C["dim"], width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=str(val), font=("Segoe UI", 12, "bold"), text_color=clr or C["text"], anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkFrame(self, height=10, fg_color="transparent").pack()


class UsageBar(ctk.CTkFrame):
    """Labeled progress bar card."""
    def __init__(self, master, title, label, pct, **kw):
        super().__init__(master, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"], **kw)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(top, text=title, font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(top, text=label, font=("Segoe UI", 12), text_color=C["dim"]).pack(side="right")
        p = max(0, min(pct / 100, 1.0))
        bc = C["green"] if p < 0.6 else C["yellow"] if p < 0.8 else C["red"]
        bar = ctk.CTkProgressBar(self, progress_color=bc, fg_color=C["bg2"], height=12, corner_radius=6)
        bar.set(p)
        bar.pack(fill="x", padx=14, pady=(0, 12))


class IssueRow(ctk.CTkFrame):
    """Single issue display row."""
    def __init__(self, master, issue: Issue, **kw):
        super().__init__(master, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"], **kw)
        sc = _scolor(issue.severity)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(top, text=f" {issue.severity.upper()} ", font=("Segoe UI", 10, "bold"), text_color="#fff", fg_color=sc, corner_radius=6, width=72).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top, text=issue.title, font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(top, text=issue.category, font=("Segoe UI", 11), text_color=C["dim"]).pack(side="right")
        ctk.CTkLabel(self, text=issue.description, font=("Segoe UI", 12), text_color=C["dim"], wraplength=650, anchor="w", justify="left").pack(fill="x", padx=14, pady=2)
        if issue.recommendation:
            ctk.CTkLabel(self, text=f"Fix: {issue.recommendation}", font=("Segoe UI", 12), text_color=C["green"], wraplength=650, anchor="w", justify="left").pack(fill="x", padx=14, pady=(0, 10))


# ─── Main Application ───────────────────────────────────────────────────────────

class PCDoctorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PC Doctor — AI System Diagnostic")
        self.geometry("1280x850")
        self.minsize(1050, 700)
        self.configure(fg_color=C["bg"])

        self.scan_results = None
        self.all_issues = []
        self.health_score = 0
        self.ai_analysis = None
        self.ai_chat_inst = None
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.monitor_running = False
        self.monitor_history = {"cpu": [], "ram": []}

        self._build_ui()

    # ────────────────────── UI SKELETON ──────────────────────────

    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=C["bg2"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(self.sidebar, text="PC DOCTOR", font=("Segoe UI", 22, "bold"), text_color=C["accent"]).pack(pady=(24, 0))
        ctk.CTkLabel(self.sidebar, text="AI System Diagnostic", font=("Segoe UI", 11), text_color=C["dim"]).pack(pady=(0, 16))
        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=(0, 10))

        self.nav_btns = {}
        pages = [
            ("home",       "Home"),
            ("monitor",    "Live Monitor"),
            ("hardware",   "Hardware"),
            ("network",    "Network & Security"),
            ("winhealth",  "Windows Health"),
            ("processes",  "Processes"),
            ("software",   "Installed Software"),
            ("drivers",    "Drivers & Services"),
            ("issues",     "Issues"),
            ("ai",         "AI Analysis"),
            ("chat",       "AI Chat"),
            ("tools",      "System Tools"),
            ("settings",   "Settings"),
        ]
        for key, label in pages:
            b = ctk.CTkButton(self.sidebar, text=f"  {label}", font=("Segoe UI", 13),
                              fg_color="transparent", hover_color=C["card"], text_color=C["dim"],
                              anchor="w", height=36, corner_radius=8,
                              command=lambda k=key: self._go(k))
            b.pack(fill="x", padx=10, pady=1)
            self.nav_btns[key] = b

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        self.scan_btn = ctk.CTkButton(self.sidebar, text="START SCAN", font=("Segoe UI", 14, "bold"),
                                      fg_color=C["accent"], hover_color=C["accent2"], text_color="#fff",
                                      height=44, corner_radius=10, command=self._start_scan)
        self.scan_btn.pack(fill="x", padx=14, pady=(6, 4))

        self.report_btn = ctk.CTkButton(self.sidebar, text="Export Report", font=("Segoe UI", 12),
                                        fg_color="transparent", hover_color=C["card"], text_color=C["dim"],
                                        border_width=1, border_color=C["border"], height=34, corner_radius=8,
                                        command=self._export_report)
        self.report_btn.pack(fill="x", padx=14, pady=(0, 14))

        # Content
        self.content = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.content.pack(side="right", fill="both", expand=True)

        self.frames = {}
        for key, _ in pages:
            f = ctk.CTkFrame(self.content, fg_color=C["bg"])
            self.frames[key] = f

        self._build_home()
        self._build_monitor()
        self._build_settings()
        self._build_tools()
        self._go("home")

    def _go(self, page):
        for f in self.frames.values():
            f.pack_forget()
        for k, b in self.nav_btns.items():
            b.configure(fg_color=C["card"] if k == page else "transparent",
                        text_color=C["accent"] if k == page else C["dim"])
        self.frames[page].pack(fill="both", expand=True)
        if page == "monitor" and self.scan_results:
            self._start_monitor()
        elif page != "monitor":
            self.monitor_running = False

    # ────────────────────── HOME ─────────────────────────────────

    def _build_home(self):
        f = self.frames["home"]
        self._home_inner = ctk.CTkFrame(f, fg_color="transparent")
        self._home_inner.pack(fill="both", expand=True)

        # Welcome
        self._welcome = ctk.CTkFrame(self._home_inner, fg_color="transparent")
        self._welcome.pack(fill="both", expand=True)
        ctk.CTkLabel(self._welcome, text="", height=60).pack()
        ctk.CTkLabel(self._welcome, text="🖥️", font=("Segoe UI", 64)).pack()
        ctk.CTkLabel(self._welcome, text="PC Doctor", font=("Segoe UI", 32, "bold"), text_color=C["text"]).pack(pady=(8, 4))
        ctk.CTkLabel(self._welcome, text="AI-powered diagnostic tool for your Windows PC\n15 deep scans • Real-time monitoring • AI chat • System tools",
                     font=("Segoe UI", 14), text_color=C["dim"], justify="center").pack(pady=(0, 24))
        ctk.CTkButton(self._welcome, text="START FULL SCAN", font=("Segoe UI", 16, "bold"),
                      fg_color=C["accent"], hover_color=C["accent2"], text_color="#fff",
                      width=280, height=50, corner_radius=12, command=self._start_scan).pack()

        # Progress
        self._prog_frame = ctk.CTkFrame(self._home_inner, fg_color="transparent")
        self._prog_lbl = ctk.CTkLabel(self._prog_frame, text="Scanning...", font=("Segoe UI", 20, "bold"), text_color=C["accent"])
        self._prog_det = ctk.CTkLabel(self._prog_frame, text="", font=("Segoe UI", 13), text_color=C["dim"])
        self._prog_bar = ctk.CTkProgressBar(self._prog_frame, progress_color=C["accent"], fg_color=C["card"], height=16, corner_radius=8, width=500)
        self._prog_bar.set(0)

        # Dashboard (after scan)
        self._dash = ctk.CTkScrollableFrame(self._home_inner, fg_color="transparent")

    # ────────────────────── LIVE MONITOR ─────────────────────────

    def _build_monitor(self):
        f = self.frames["monitor"]
        self._mon_inner = ctk.CTkScrollableFrame(f, fg_color="transparent")
        self._mon_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(self._mon_inner, text="Live System Monitor", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        self._mon_status = ctk.CTkLabel(self._mon_inner, text="Run a scan first to enable live monitoring", font=("Segoe UI", 12), text_color=C["dim"])
        self._mon_status.pack(anchor="w", pady=(0, 12))

        self._mon_cards_frame = ctk.CTkFrame(self._mon_inner, fg_color="transparent")
        self._mon_cards_frame.pack(fill="x", pady=(0, 12))

        # CPU bar
        self._mon_cpu_frame = ctk.CTkFrame(self._mon_inner, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        self._mon_cpu_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self._mon_cpu_frame, text="CPU Usage (per core)", font=("Segoe UI", 14, "bold"), text_color=C["cyan"]).pack(anchor="w", padx=16, pady=(12, 6))
        self._mon_cpu_bars = ctk.CTkFrame(self._mon_cpu_frame, fg_color="transparent")
        self._mon_cpu_bars.pack(fill="x", padx=16, pady=(0, 14))

        # History
        self._mon_hist_frame = ctk.CTkFrame(self._mon_inner, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        self._mon_hist_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self._mon_hist_frame, text="Usage History (last 60 samples)", font=("Segoe UI", 14, "bold"), text_color=C["purple"]).pack(anchor="w", padx=16, pady=(12, 6))
        self._mon_canvas = tk.Canvas(self._mon_hist_frame, bg=C["bg2"], highlightthickness=0, height=150)
        self._mon_canvas.pack(fill="x", padx=16, pady=(0, 14))

    def _start_monitor(self):
        if self.monitor_running:
            return
        self.monitor_running = True
        self._mon_status.configure(text="Live updating every 2 seconds...")
        self._update_monitor()

    def _update_monitor(self):
        if not self.monitor_running:
            return
        try:
            snap = RealTimeMonitor.get_snapshot()
            self.monitor_history["cpu"].append(snap["cpu_percent"])
            self.monitor_history["ram"].append(snap["ram_percent"])
            if len(self.monitor_history["cpu"]) > 60:
                self.monitor_history["cpu"] = self.monitor_history["cpu"][-60:]
                self.monitor_history["ram"] = self.monitor_history["ram"][-60:]

            # Update stat cards
            for w in self._mon_cards_frame.winfo_children():
                w.destroy()
            cards_data = [
                ("CPU", f"{snap['cpu_percent']}%", snap["cpu_percent"]),
                ("RAM", f"{snap['ram_percent']}%", snap["ram_percent"]),
                ("Disk", f"{snap['disk_percent']}%", snap["disk_percent"]),
                ("Net Sent", f"{snap['net_sent_mb']} MB", None),
                ("Net Recv", f"{snap['net_recv_mb']} MB", None),
            ]
            for title, val, bar_p in cards_data:
                clr = C["green"]
                if bar_p is not None:
                    clr = C["green"] if bar_p < 60 else C["yellow"] if bar_p < 80 else C["red"]
                sc = StatCard(self._mon_cards_frame, title, val, color=clr, bar_pct=bar_p)
                sc.pack(side="left", fill="x", expand=True, padx=(0, 6))

            # Per-core CPU bars
            for w in self._mon_cpu_bars.winfo_children():
                w.destroy()
            cores = snap.get("cpu_per_core", [])
            for i, pct in enumerate(cores):
                row = ctk.CTkFrame(self._mon_cpu_bars, fg_color="transparent", height=18)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)
                ctk.CTkLabel(row, text=f"Core {i}", font=("Segoe UI", 10), text_color=C["dim"], width=55).pack(side="left")
                p = max(0, min(pct / 100, 1.0))
                bc = C["green"] if p < 0.6 else C["yellow"] if p < 0.8 else C["red"]
                bar = ctk.CTkProgressBar(row, progress_color=bc, fg_color=C["bg2"], height=10, corner_radius=5)
                bar.set(p)
                bar.pack(side="left", fill="x", expand=True, padx=(4, 4))
                ctk.CTkLabel(row, text=f"{pct:.0f}%", font=("Segoe UI", 10, "bold"), text_color=bc, width=40).pack(side="right")

            # Draw history chart
            self._draw_history()

        except Exception:
            pass

        if self.monitor_running:
            self.after(2000, self._update_monitor)

    def _draw_history(self):
        c = self._mon_canvas
        c.delete("all")
        w = c.winfo_width() or 600
        h = 150
        cpu_hist = self.monitor_history["cpu"]
        ram_hist = self.monitor_history["ram"]
        if len(cpu_hist) < 2:
            return
        n = len(cpu_hist)
        dx = w / max(n - 1, 1)

        # Grid
        for yp in (25, 50, 75):
            y = h - (yp / 100 * h)
            c.create_line(0, y, w, y, fill="#374151", dash=(2, 4))
            c.create_text(w - 4, y - 8, text=f"{yp}%", fill="#6b7280", font=("Segoe UI", 8), anchor="e")

        # CPU line
        cpu_pts = []
        for i, v in enumerate(cpu_hist):
            cpu_pts.extend([i * dx, h - (v / 100 * h)])
        if len(cpu_pts) >= 4:
            c.create_line(*cpu_pts, fill="#22d3ee", width=2, smooth=True)

        # RAM line
        ram_pts = []
        for i, v in enumerate(ram_hist):
            ram_pts.extend([i * dx, h - (v / 100 * h)])
        if len(ram_pts) >= 4:
            c.create_line(*ram_pts, fill="#a78bfa", width=2, smooth=True)

        # Legend
        c.create_rectangle(8, 6, 18, 14, fill="#22d3ee", outline="")
        c.create_text(22, 10, text="CPU", fill="#22d3ee", font=("Segoe UI", 9), anchor="w")
        c.create_rectangle(58, 6, 68, 14, fill="#a78bfa", outline="")
        c.create_text(72, 10, text="RAM", fill="#a78bfa", font=("Segoe UI", 9), anchor="w")

    # ────────────────────── SETTINGS ─────────────────────────────

    def _build_settings(self):
        f = self.frames["settings"]
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="Settings", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 14))

        card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(card, text="OpenAI API Key", font=("Segoe UI", 14, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(14, 2))
        ctk.CTkLabel(card, text="For AI-powered analysis and chat. Without it, built-in offline analysis is used.", font=("Segoe UI", 11), text_color=C["dim"]).pack(anchor="w", padx=16, pady=(0, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 14))
        self.api_entry = ctk.CTkEntry(row, placeholder_text="sk-...", font=("Segoe UI", 12), fg_color=C["bg"], border_color=C["border"], height=36, show="*")
        self.api_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        if self.api_key:
            self.api_entry.insert(0, self.api_key)
        ctk.CTkButton(row, text="Save", width=80, height=36, fg_color=C["green"], hover_color="#16a34a", command=self._save_key).pack(side="right")

        about = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        about.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(about, text="About", font=("Segoe UI", 14, "bold"), text_color=C["accent"]).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(about, text="PC Doctor v2.0 — AI-Powered System Diagnostic\n15 Scanners • Real-Time Monitor • AI Chat • System Tools\nBuilt with Python • CustomTkinter • psutil • WMI • OpenAI",
                     font=("Segoe UI", 12), text_color=C["dim"], justify="left").pack(anchor="w", padx=16, pady=(0, 14))

    def _save_key(self):
        self.api_key = self.api_entry.get().strip()
        os.environ["OPENAI_API_KEY"] = self.api_key
        messagebox.showinfo("PC Doctor", "API key saved for this session.")

    # ────────────────────── SYSTEM TOOLS ─────────────────────────

    def _build_tools(self):
        f = self.frames["tools"]
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="System Tools", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Quick maintenance and repair tools", font=("Segoe UI", 12), text_color=C["dim"]).pack(anchor="w", pady=(0, 14))

        self._tools_log = None

        tools = [
            ("Clean Temp Files", "Delete temporary files to free disk space", C["green"], self._tool_clean_temp),
            ("Flush DNS Cache", "Reset DNS resolver cache to fix connection issues", C["cyan"], self._tool_flush_dns),
            ("Reset Network", "Release IP, flush DNS, renew IP, reset Winsock", C["accent"], self._tool_reset_network),
            ("Launch Disk Cleanup", "Open Windows Disk Cleanup utility", C["yellow"], self._tool_disk_cleanup),
            ("Check Disk (C:)", "Run check disk on C: drive", C["orange"], self._tool_check_disk),
            ("Open Task Manager", "Launch Windows Task Manager", C["purple"], lambda: SystemTools.open_task_manager()),
            ("Open Device Manager", "Manage hardware drivers", C["pink"], lambda: SystemTools.open_device_manager()),
            ("Open Event Viewer", "View Windows event logs", C["cyan"], lambda: SystemTools.open_event_viewer()),
            ("Open Disk Management", "Manage disk partitions", C["yellow"], lambda: SystemTools.open_disk_management()),
            ("Open System Information", "Detailed system info (msinfo32)", C["dim"], lambda: SystemTools.open_system_info()),
        ]

        for title, desc, color, cmd in tools:
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
            card.pack(fill="x", pady=(0, 6))
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=10)
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(left, text=title, font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=desc, font=("Segoe UI", 11), text_color=C["dim"]).pack(anchor="w")
            ctk.CTkButton(row, text="Run", width=70, height=32, fg_color=color, hover_color=C["card2"],
                          corner_radius=8, command=cmd).pack(side="right")

        ctk.CTkLabel(scroll, text="Output Log", font=("Segoe UI", 14, "bold"), text_color=C["dim"]).pack(anchor="w", pady=(14, 6))
        self._tools_log = ctk.CTkTextbox(scroll, fg_color=C["bg2"], text_color=C["text"], font=("Consolas", 12),
                                         corner_radius=10, border_width=1, border_color=C["border"], height=200, wrap="word")
        self._tools_log.pack(fill="x")
        self._tools_log.insert("end", "Ready. Click a tool to run it.\n")
        self._tools_log.configure(state="disabled")

    def _log_tool(self, msg):
        if self._tools_log:
            self._tools_log.configure(state="normal")
            self._tools_log.insert("end", f"\n[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self._tools_log.configure(state="disabled")
            self._tools_log.see("end")

    def _tool_clean_temp(self):
        self._log_tool("Cleaning temp files...")
        def do():
            r = SystemTools.clean_temp_files()
            self.after(0, lambda: self._log_tool(f"Done! Cleaned {r['cleaned_files']} files, freed {r['freed_mb']} MB"))
        threading.Thread(target=do, daemon=True).start()

    def _tool_flush_dns(self):
        self._log_tool("Flushing DNS cache...")
        def do():
            r = SystemTools.flush_dns()
            self.after(0, lambda: self._log_tool(f"{'Success' if r['success'] else 'Failed'}: {r['output']}"))
        threading.Thread(target=do, daemon=True).start()

    def _tool_reset_network(self):
        self._log_tool("Resetting network stack...")
        def do():
            r = SystemTools.reset_network()
            self.after(0, lambda: self._log_tool(r["output"]))
        threading.Thread(target=do, daemon=True).start()

    def _tool_disk_cleanup(self):
        SystemTools.run_disk_cleanup()
        self._log_tool("Disk Cleanup launched.")

    def _tool_check_disk(self):
        self._log_tool("Running check disk on C:...")
        def do():
            r = SystemTools.check_disk("C")
            self.after(0, lambda: self._log_tool(r["output"][:500]))
        threading.Thread(target=do, daemon=True).start()

    # ────────────────────── SCAN LOGIC ───────────────────────────

    def _start_scan(self):
        self.scan_btn.configure(state="disabled", text="SCANNING...")
        self._welcome.pack_forget()
        self._dash.pack_forget()
        self._prog_frame.pack(fill="both", expand=True)
        self._prog_lbl.pack(pady=(120, 8))
        self._prog_bar.pack(pady=(0, 8))
        self._prog_det.pack()
        self._prog_bar.set(0)
        self._go("home")
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        scanner = MasterScanner()
        scan_labels = {
            "system": "System Information", "cpu": "CPU & Processor", "memory": "Memory / RAM",
            "disk": "Storage & Disks", "network": "Network & Internet", "gpu": "Graphics / GPU",
            "processes": "Running Processes", "security": "Security & Firewall", "battery": "Battery",
            "startup": "Startup Programs", "installed_software": "Installed Software",
            "drivers": "Drivers", "services": "Windows Services", "temp_files": "Temp Files",
            "reliability": "Windows Reliability Monitor", "windows_update": "Windows Update History",
            "system_health": "System File Integrity", "event_logs": "Event Logs",
        }
        results = {}
        total = len(scanner.scanners)
        for i, (name, scan_obj) in enumerate(scanner.scanners.items()):
            lbl = scan_labels.get(name, name)
            self.after(0, lambda l=lbl, p=i/total: self._prog_update(l, p))
            results[name] = scan_obj.scan()

        self.after(0, lambda: self._prog_update("AI Analysis...", 0.96))
        health = scanner.calculate_overall_health(results)
        issues = scanner.get_all_issues(results)
        ai = AIAnalyzer(api_key=self.api_key)
        analysis = ai.analyze(results, issues, health)

        self.scan_results = results
        self.all_issues = issues
        self.health_score = health
        self.ai_analysis = analysis

        self.after(0, self._scan_done)

    def _prog_update(self, label, pct):
        self._prog_lbl.configure(text="Scanning your system...")
        self._prog_det.configure(text=label)
        self._prog_bar.set(pct)

    def _scan_done(self):
        self.scan_btn.configure(state="normal", text="RE-SCAN")
        self._prog_frame.pack_forget()

        self._fill_dashboard()
        self._fill_hardware()
        self._fill_network()
        self._fill_winhealth()
        self._fill_processes()
        self._fill_software()
        self._fill_drivers()
        self._fill_issues()
        self._fill_ai()
        self._fill_chat()

        self._dash.pack(fill="both", expand=True)
        self._go("home")

    # ────────────────────── DASHBOARD ────────────────────────────

    def _fill_dashboard(self):
        for w in self._dash.winfo_children():
            w.destroy()

        score = self.health_score
        color = _hcolor(score)
        label = _hlabel(score)

        # Score header
        hdr = ctk.CTkFrame(self._dash, fg_color=C["card"], corner_radius=14, border_width=1, border_color=C["border"], height=130)
        hdr.pack(fill="x", padx=20, pady=(16, 12))
        hdr.pack_propagate(False)
        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", padx=24, fill="y")
        ctk.CTkLabel(left, text=f"{score:.0f}", font=("Segoe UI", 48, "bold"), text_color=color).pack(side="left", pady=16)
        ctk.CTkLabel(left, text=" /100", font=("Segoe UI", 18), text_color=C["dim"]).pack(side="left", anchor="s", pady=30)
        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="left", padx=16, fill="y")
        ctk.CTkLabel(right, text=label, font=("Segoe UI", 20, "bold"), text_color=color).pack(anchor="w", pady=(24, 2))
        crit = len([i for i in self.all_issues if i.severity == "critical"])
        warn = len([i for i in self.all_issues if i.severity == "warning"])
        info = len([i for i in self.all_issues if i.severity == "info"])
        ctk.CTkLabel(right, text=f"{crit} Critical  •  {warn} Warnings  •  {info} Info  •  15 Scans Complete", font=("Segoe UI", 12), text_color=C["dim"]).pack(anchor="w")

        # Quick stat cards
        row = ctk.CTkFrame(self._dash, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 10))
        for title, val, clr, bp in self._quick_stats():
            StatCard(row, title, val, color=clr, bar_pct=bp).pack(side="left", fill="x", expand=True, padx=(0, 6))

        # AI summary
        assess = self.ai_analysis.get("overall_assessment", "")
        if assess:
            ai_c = ctk.CTkFrame(self._dash, fg_color=C["card"], corner_radius=12, border_width=1, border_color="#3730a3")
            ai_c.pack(fill="x", padx=20, pady=(0, 10))
            ctk.CTkLabel(ai_c, text="AI Assessment", font=("Segoe UI", 14, "bold"), text_color=C["purple"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(ai_c, text=assess, font=("Segoe UI", 12), text_color="#c4b5fd", wraplength=700, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        # Top issues
        if self.all_issues:
            ctk.CTkLabel(self._dash, text="Top Issues", font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(anchor="w", padx=20, pady=(4, 6))
            for issue in self.all_issues[:6]:
                IssueRow(self._dash, issue).pack(fill="x", padx=20, pady=(0, 5))

    def _quick_stats(self):
        stats = []
        r = self.scan_results
        cpu = r.get("cpu")
        if cpu:
            v = cpu.data.get("average_usage_percent", 0)
            stats.append(("CPU", f"{v}%", C["green"] if v < 60 else C["yellow"] if v < 85 else C["red"], v))
        mem = r.get("memory")
        if mem:
            v = mem.data.get("usage_percent", 0)
            stats.append(("RAM", f"{v}%", C["green"] if v < 65 else C["yellow"] if v < 85 else C["red"], v))
        disk = r.get("disk")
        if disk and disk.data.get("partitions"):
            v = disk.data["partitions"][0].get("usage_percent", 0)
            stats.append(("Disk", f"{v}%", C["green"] if v < 75 else C["yellow"] if v < 90 else C["red"], v))
        net = r.get("network")
        if net:
            c = net.data.get("internet_connected", False)
            stats.append(("Internet", "Online" if c else "Offline", C["green"] if c else C["red"], None))
        tmp = r.get("temp_files")
        if tmp:
            sz = tmp.data.get("total_size_mb", 0)
            stats.append(("Temp Files", f"{sz} MB", C["yellow"] if sz > 500 else C["green"], None))
        rel = r.get("reliability")
        if rel:
            si = rel.data.get("stability_index")
            if si is not None:
                sc = C["green"] if si >= 8 else C["yellow"] if si >= 5 else C["red"]
                stats.append(("Stability", f"{si:.1f}/10", sc, None))
        wu = r.get("windows_update")
        if wu:
            fc = wu.data.get("failed_count", 0)
            if fc > 0:
                stats.append(("Updates", f"{fc} Failed", C["red"], None))
        return stats

    # ────────────────────── HARDWARE ─────────────────────────────

    def _fill_hardware(self):
        f = self.frames["hardware"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)
        ctk.CTkLabel(scroll, text="Hardware Details", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 14))

        r = self.scan_results

        # System
        sd = r.get("system")
        if sd:
            d = sd.data
            InfoTable(scroll, "System", [
                ("OS", d.get("os_name", d.get("os_edition", "N/A")), None),
                ("Build", d.get("build_number", d.get("os_version", "N/A")), None),
                ("Hostname", d.get("hostname", "N/A"), None),
                ("Architecture", d.get("architecture", "N/A"), None),
                ("Uptime", d.get("uptime_human", "N/A"), None),
                ("Motherboard", f"{d.get('motherboard_manufacturer', '')} {d.get('motherboard', 'N/A')}", None),
                ("BIOS", f"{d.get('bios_manufacturer', '')} {d.get('bios_version', 'N/A')}", None),
            ]).pack(fill="x", pady=(0, 10))

        # CPU
        cd = r.get("cpu")
        if cd:
            d = cd.data
            u = d.get("average_usage_percent", 0)
            uc = C["green"] if u < 60 else C["yellow"] if u < 85 else C["red"]
            items = [
                ("Processor", str(d.get("processor", "N/A"))[:60], None),
                ("Cores", f"{d.get('physical_cores', '?')}P / {d.get('logical_cores', '?')}L", None),
                ("Frequency", f"{d.get('current_frequency_mhz', 'N/A')} MHz (Max: {d.get('max_frequency_mhz', 'N/A')})", None),
                ("Usage", f"{u}%", uc),
            ]
            t = d.get("temperature_celsius")
            if t:
                tc = C["green"] if t < 65 else C["yellow"] if t < 80 else C["red"]
                items.append(("Temperature", f"{t}°C", tc))
            InfoTable(scroll, "CPU", items, accent=C["cyan"]).pack(fill="x", pady=(0, 6))
            UsageBar(scroll, "CPU Usage", f"{u}%", u).pack(fill="x", pady=(0, 10))

        # Memory
        md = r.get("memory")
        if md:
            d = md.data
            p = d.get("usage_percent", 0)
            mc = C["green"] if p < 65 else C["yellow"] if p < 85 else C["red"]
            InfoTable(scroll, "Memory", [
                ("Total", f"{d.get('total_gb', 'N/A')} GB", None),
                ("Used", f"{d.get('used_gb', 'N/A')} GB", None),
                ("Available", f"{d.get('available_gb', 'N/A')} GB", None),
                ("Usage", f"{p}%", mc),
                ("Swap", f"{d.get('swap_used_gb', 'N/A')} / {d.get('swap_total_gb', 'N/A')} GB", None),
            ], accent=C["purple"]).pack(fill="x", pady=(0, 6))
            UsageBar(scroll, "RAM", f"{d.get('used_gb', 0)} / {d.get('total_gb', 0)} GB", p).pack(fill="x", pady=(0, 10))

        # Disks
        dd = r.get("disk")
        if dd:
            for part in dd.data.get("partitions", []):
                p = part.get("usage_percent", 0)
                dc = C["green"] if p < 75 else C["yellow"] if p < 90 else C["red"]
                InfoTable(scroll, f"Drive {part.get('mountpoint', '?')}", [
                    ("Device", part.get("device", "N/A"), None),
                    ("Filesystem", part.get("filesystem", "N/A"), None),
                    ("Total", f"{part.get('total_gb', '?')} GB", None),
                    ("Free", f"{part.get('free_gb', '?')} GB", None),
                    ("Usage", f"{p}%", dc),
                ], accent=C["green"]).pack(fill="x", pady=(0, 6))
                UsageBar(scroll, f"Disk {part.get('mountpoint', '?')}", f"{part.get('free_gb', '?')} GB free", p).pack(fill="x", pady=(0, 10))

        # GPU
        gd = r.get("gpu")
        if gd and gd.data.get("gpus"):
            for g in gd.data["gpus"]:
                items = [("Name", g.get("name", "N/A"), None)]
                if g.get("memory_total_mb"):
                    items.append(("VRAM", f"{g.get('memory_used_mb', 0):.0f} / {g.get('memory_total_mb', 0):.0f} MB", None))
                if g.get("temperature_celsius"):
                    tc = C["green"] if g["temperature_celsius"] < 70 else C["yellow"] if g["temperature_celsius"] < 85 else C["red"]
                    items.append(("Temperature", f"{g['temperature_celsius']}°C", tc))
                if g.get("driver_version"): items.append(("Driver", str(g["driver_version"]), None))
                if g.get("video_memory_mb"): items.append(("Video RAM", f"{g['video_memory_mb']:.0f} MB", None))
                InfoTable(scroll, "GPU", items, accent=C["yellow"]).pack(fill="x", pady=(0, 10))

        # Battery
        bd = r.get("battery")
        if bd and bd.data.get("present"):
            d = bd.data
            InfoTable(scroll, "Battery", [
                ("Charge", f"{d.get('percent', '?')}%", None),
                ("Plugged In", "Yes" if d.get("plugged_in") else "No", C["green"] if d.get("plugged_in") else C["yellow"]),
                ("Time Left", f"{d.get('time_remaining_min', 'N/A')} min", None),
            ], accent=C["green"]).pack(fill="x", pady=(0, 10))

    # ────────────────────── NETWORK & SECURITY ───────────────────

    def _fill_network(self):
        f = self.frames["network"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)
        ctk.CTkLabel(scroll, text="Network & Security", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 14))

        net = self.scan_results.get("network")
        if net:
            d = net.data
            cn = d.get("internet_connected", False)
            dn = d.get("dns_working", False)
            InfoTable(scroll, "Network", [
                ("Internet", "Connected" if cn else "DISCONNECTED", C["green"] if cn else C["red"]),
                ("DNS", "Working" if dn else "FAILED", C["green"] if dn else C["red"]),
                ("Latency", f"{d.get('latency_ms', 'N/A')} ms", None),
                ("Data Sent", f"{d.get('bytes_sent_gb', 'N/A')} GB", None),
                ("Data Received", f"{d.get('bytes_recv_gb', 'N/A')} GB", None),
                ("Errors (In/Out)", f"{d.get('errors_in', 0)} / {d.get('errors_out', 0)}", C["red"] if (d.get('errors_in', 0) + d.get('errors_out', 0)) > 50 else None),
            ]).pack(fill="x", pady=(0, 10))

        sec = self.scan_results.get("security")
        if sec:
            d = sec.data
            fw = d.get("firewall_enabled", False)
            df = d.get("windows_defender", {})
            av = df.get("enabled", True) if isinstance(df, dict) else True
            rt = df.get("realtime_protection", True) if isinstance(df, dict) else True
            InfoTable(scroll, "Security", [
                ("Firewall", "ENABLED" if fw else "DISABLED", C["green"] if fw else C["red"]),
                ("Defender", "Active" if av else "DISABLED", C["green"] if av else C["red"]),
                ("Real-time", "Active" if rt else "OFF", C["green"] if rt else C["red"]),
                ("UAC", "Enabled" if d.get("uac_enabled") else "Disabled", C["green"] if d.get("uac_enabled") else C["red"]),
            ], accent=C["red"]).pack(fill="x", pady=(0, 10))

        st = self.scan_results.get("startup")
        if st:
            items = [("Total", str(st.data.get("count", 0)), None)]
            for p in st.data.get("startup_programs", [])[:12]:
                items.append((p["name"][:35], p["command"][:55], C["dim"]))
            InfoTable(scroll, "Startup Programs", items, accent=C["orange"]).pack(fill="x", pady=(0, 10))

    # ────────────────────── WINDOWS HEALTH ─────────────────────

    def _fill_winhealth(self):
        f = self.frames["winhealth"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)
        ctk.CTkLabel(scroll, text="Windows Health & Reliability", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Data from Windows' own diagnostic systems", font=("Segoe UI", 12), text_color=C["dim"]).pack(anchor="w", pady=(0, 14))

        # Reliability Monitor
        rel = self.scan_results.get("reliability")
        if rel:
            d = rel.data
            si = d.get("stability_index")
            si_str = f"{si:.1f}/10" if si is not None else "N/A"
            si_c = C["green"] if si and si >= 8 else C["yellow"] if si and si >= 5 else C["red"] if si else C["dim"]
            InfoTable(scroll, "Windows Reliability Monitor", [
                ("Stability Index", si_str, si_c),
                ("Total Failures (30 days)", str(d.get("total_failures_30d", 0)), C["red"] if d.get("total_failures_30d", 0) > 5 else None),
                ("Problem Reports", str(d.get("total_problem_reports", 0)), C["yellow"] if d.get("total_problem_reports", 0) > 5 else None),
            ], accent=C["purple"]).pack(fill="x", pady=(0, 10))

            records = d.get("failure_records", [])
            if records:
                items = []
                for r in records[:15]:
                    tc = C["red"] if r.get("type") == "Hardware" else C["yellow"]
                    items.append((f"[{r.get('type', '?')}] {r.get('source', 'Unknown')[:30]}", r.get("message", "")[:80], tc))
                InfoTable(scroll, f"Recent Failure Records ({len(records)} total)", items, accent=C["red"]).pack(fill="x", pady=(0, 10))

            reports = d.get("problem_reports", [])
            if reports:
                items = [(r.get("app", "Unknown")[:35], r.get("time", ""), C["dim"]) for r in reports[:12]]
                InfoTable(scroll, f"Windows Problem Reports ({len(reports)})", items, accent=C["orange"]).pack(fill="x", pady=(0, 10))

        # Windows Update
        wu = self.scan_results.get("windows_update")
        if wu:
            d = wu.data
            items = [
                ("Recent Updates", str(d.get("total_recent", 0)), None),
                ("Succeeded", str(d.get("succeeded_count", 0)), C["green"]),
                ("Failed", str(d.get("failed_count", 0)), C["red"] if d.get("failed_count", 0) > 0 else C["green"]),
                ("Pending", str(d.get("pending_count", 0)), C["yellow"] if d.get("pending_count", 0) > 0 else None),
            ]
            InfoTable(scroll, "Windows Update", items, accent=C["accent"]).pack(fill="x", pady=(0, 10))

            failed = d.get("failed_updates", [])
            if failed:
                items = [(u.get("title", "?")[:60], u.get("date", "")[:20], C["red"]) for u in failed[:8]]
                InfoTable(scroll, f"Failed Updates ({len(failed)})", items, accent=C["red"]).pack(fill="x", pady=(0, 10))

        # System Health
        sh = self.scan_results.get("system_health")
        if sh:
            d = sh.data
            sfc = d.get("sfc_status", {})
            dism = d.get("component_store", {})

            sfc_text = "Corrupted files found!" if sfc.get("corrupted") else "Repaired" if sfc.get("repaired") else "OK"
            sfc_c = C["red"] if sfc.get("corrupted") else C["yellow"] if sfc.get("repaired") else C["green"]
            dism_text = "Needs repair" if dism.get("repairable") else "Healthy" if dism.get("healthy") else "Unknown"
            dism_c = C["red"] if dism.get("repairable") else C["green"] if dism.get("healthy") else C["dim"]

            InfoTable(scroll, "System File Integrity", [
                ("System Files (SFC)", sfc_text, sfc_c),
                ("SFC Detail", sfc.get("detail", "No issues")[:80], C["dim"]),
                ("Component Store (DISM)", dism_text, dism_c),
            ], accent=C["cyan"]).pack(fill="x", pady=(0, 10))

            perf = d.get("performance_issues", [])
            if perf:
                items = [(p.get("title", "")[:40], p.get("description", "")[:60], C["yellow"]) for p in perf]
                InfoTable(scroll, "Performance Issues", items, accent=C["yellow"]).pack(fill="x", pady=(0, 10))

            ac = d.get("action_center_items", [])
            if ac:
                items = [(a.get("title", "")[:40], a.get("description", "")[:60], C["red"] if a.get("severity") == "critical" else C["yellow"]) for a in ac]
                InfoTable(scroll, "Windows Security Alerts", items, accent=C["red"]).pack(fill="x", pady=(0, 10))

    # ────────────────────── PROCESSES ────────────────────────────

    def _fill_processes(self):
        f = self.frames["processes"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        proc = self.scan_results.get("processes")
        if not proc: return
        d = proc.data
        ctk.CTkLabel(scroll, text="Processes", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text=f"Total: {d.get('total_processes', '?')} running", font=("Segoe UI", 13), text_color=C["dim"]).pack(anchor="w", pady=(0, 14))

        cpu_items = [(f"PID {p['pid']} — {p['name']}", f"{p['cpu_percent']:.1f}%",
                      C["red"] if p['cpu_percent'] > 50 else C["yellow"] if p['cpu_percent'] > 20 else C["text"])
                     for p in d.get("top_cpu_consumers", [])]
        if cpu_items:
            InfoTable(scroll, "Top CPU Consumers", cpu_items, accent=C["cyan"]).pack(fill="x", pady=(0, 10))

        mem_items = [(f"PID {p['pid']} — {p['name']}", f"{p['memory_percent']:.1f}%",
                      C["red"] if p['memory_percent'] > 15 else C["yellow"] if p['memory_percent'] > 5 else C["text"])
                     for p in d.get("top_memory_consumers", [])]
        if mem_items:
            InfoTable(scroll, "Top Memory Consumers", mem_items, accent=C["purple"]).pack(fill="x", pady=(0, 10))

    # ────────────────────── INSTALLED SOFTWARE ───────────────────

    def _fill_software(self):
        f = self.frames["software"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        sw = self.scan_results.get("installed_software")
        if not sw: return
        programs = sw.data.get("programs", [])
        ctk.CTkLabel(scroll, text="Installed Software", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text=f"{len(programs)} programs installed", font=("Segoe UI", 13), text_color=C["dim"]).pack(anchor="w", pady=(0, 10))

        # Search
        self._sw_search = ctk.CTkEntry(scroll, placeholder_text="Search programs...", font=("Segoe UI", 13), fg_color=C["bg"], border_color=C["border"], height=36)
        self._sw_search.pack(fill="x", pady=(0, 10))
        self._sw_list_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._sw_list_frame.pack(fill="x")
        self._sw_programs = programs
        self._sw_search.bind("<KeyRelease>", lambda e: self._filter_software())
        self._render_software(programs[:80])

    def _filter_software(self):
        q = self._sw_search.get().lower()
        filtered = [p for p in self._sw_programs if q in p["name"].lower() or q in p.get("publisher", "").lower()]
        self._render_software(filtered[:80])

    def _render_software(self, programs):
        for w in self._sw_list_frame.winfo_children(): w.destroy()
        for p in programs:
            row = ctk.CTkFrame(self._sw_list_frame, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["border"], height=36)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=p["name"][:45], font=("Segoe UI", 12), text_color=C["text"], width=320, anchor="w").pack(side="left", padx=(12, 4))
            ctk.CTkLabel(row, text=p.get("version", "")[:15], font=("Segoe UI", 11), text_color=C["dim"], width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=p.get("publisher", "")[:25], font=("Segoe UI", 11), text_color=C["dim"], width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=p.get("size", ""), font=("Segoe UI", 11), text_color=C["dim"], width=80, anchor="e").pack(side="right", padx=12)

    # ────────────────────── DRIVERS & SERVICES ───────────────────

    def _fill_drivers(self):
        f = self.frames["drivers"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="Drivers & Services", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 14))

        drv = self.scan_results.get("drivers")
        if drv:
            prob = drv.data.get("problem_drivers", [])
            if prob:
                items = [(d["name"], f"Error code: {d['error_code']}", C["red"]) for d in prob]
                InfoTable(scroll, f"Problem Drivers ({len(prob)})", items, accent=C["red"]).pack(fill="x", pady=(0, 10))
            else:
                InfoTable(scroll, "Drivers", [("Status", "All drivers OK", C["green"]), ("Total", str(drv.data.get("total_drivers", 0)), None)], accent=C["green"]).pack(fill="x", pady=(0, 10))

        svc = self.scan_results.get("services")
        if svc:
            d = svc.data
            InfoTable(scroll, "Windows Services", [
                ("Total", str(d.get("total_services", 0)), None),
                ("Running", str(d.get("running_count", 0)), C["green"]),
                ("Stopped", str(d.get("stopped_count", 0)), C["dim"]),
            ], accent=C["cyan"]).pack(fill="x", pady=(0, 10))

            stopped_crit = d.get("critical_stopped", [])
            if stopped_crit:
                items = [(s["display_name"], s["state"], C["red"]) for s in stopped_crit]
                InfoTable(scroll, "Critical Services NOT Running", items, accent=C["red"]).pack(fill="x", pady=(0, 10))

        tmp = self.scan_results.get("temp_files")
        if tmp:
            d = tmp.data
            items = [("Total Size", f"{d.get('total_size_mb', 0)} MB ({d.get('total_size_gb', 0)} GB)", C["yellow"] if d.get("total_size_mb", 0) > 500 else None),
                     ("Total Files", str(d.get("total_files", 0)), None)]
            for name, info in d.get("breakdown", {}).items():
                items.append((name, f"{info.get('size_mb', 0)} MB ({info.get('file_count', 0)} files)", C["dim"]))
            InfoTable(scroll, "Temporary Files", items, accent=C["orange"]).pack(fill="x", pady=(0, 10))

    # ────────────────────── ISSUES ───────────────────────────────

    def _fill_issues(self):
        f = self.frames["issues"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        crit = [i for i in self.all_issues if i.severity == "critical"]
        warn = [i for i in self.all_issues if i.severity == "warning"]
        infos = [i for i in self.all_issues if i.severity == "info"]

        ctk.CTkLabel(scroll, text="All Issues", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text=f"{len(crit)} Critical  •  {len(warn)} Warnings  •  {len(infos)} Info", font=("Segoe UI", 13), text_color=C["dim"]).pack(anchor="w", pady=(0, 14))

        if not self.all_issues:
            ctk.CTkLabel(scroll, text="No issues found! Your system is healthy.", font=("Segoe UI", 16), text_color=C["green"]).pack(pady=40)
            return

        groups = [("CRITICAL", crit, C["red"]), ("WARNINGS", warn, C["yellow"]), ("INFO", infos, C["accent"])]
        for label, items, color in groups:
            if items:
                ctk.CTkLabel(scroll, text=f"{label} ({len(items)})", font=("Segoe UI", 15, "bold"), text_color=color).pack(anchor="w", pady=(10, 6))
                for issue in items:
                    IssueRow(scroll, issue).pack(fill="x", pady=(0, 4))

    # ────────────────────── AI ANALYSIS ──────────────────────────

    def _fill_ai(self):
        f = self.frames["ai"]
        for w in f.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="AI Analysis", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text=f"Engine: {self.ai_analysis.get('analysis_type', '?')}", font=("Segoe UI", 12), text_color=C["dim"]).pack(anchor="w", pady=(0, 14))

        assess = self.ai_analysis.get("overall_assessment", "")
        if assess:
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12, border_width=1, border_color="#3730a3")
            card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(card, text=f"Rating: {self.ai_analysis.get('health_rating', '')}", font=("Segoe UI", 16, "bold"), text_color=C["purple"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(card, text=assess, font=("Segoe UI", 12), text_color="#c4b5fd", wraplength=680, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        for item in self.ai_analysis.get("critical_issues", []):
            p = item.get("priority", "medium")
            pc = C["red"] if p == "immediate" else C["yellow"] if p == "high" else C["accent"]
            card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
            card.pack(fill="x", pady=(0, 5))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 3))
            ctk.CTkLabel(top, text=f" {p.upper()} ", font=("Segoe UI", 10, "bold"), fg_color=pc, text_color="#fff", corner_radius=6).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(top, text=item.get("issue", ""), font=("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left")
            if item.get("solution"):
                ctk.CTkLabel(card, text=f"Solution: {item['solution']}", font=("Segoe UI", 12), text_color=C["green"], wraplength=660, justify="left").pack(fill="x", padx=14, pady=(0, 10))

        tips = self.ai_analysis.get("optimization_tips", [])
        if tips:
            ctk.CTkLabel(scroll, text="Optimization Tips", font=("Segoe UI", 16, "bold"), text_color=C["text"]).pack(anchor="w", pady=(10, 8))
            for tip in tips:
                card = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["border"])
                card.pack(fill="x", pady=(0, 4))
                ctk.CTkLabel(card, text=tip.get("area", ""), font=("Segoe UI", 12, "bold"), text_color=C["purple"]).pack(anchor="w", padx=14, pady=(10, 2))
                ctk.CTkLabel(card, text=tip.get("tip", ""), font=("Segoe UI", 12), text_color=C["dim"], wraplength=660, justify="left").pack(anchor="w", padx=14, pady=(0, 2))
                ctk.CTkLabel(card, text=tip.get("expected_improvement", ""), font=("Segoe UI", 11), text_color=C["green"]).pack(anchor="w", padx=14, pady=(0, 10))

        hw = self.ai_analysis.get("hardware_recommendations", "")
        if hw:
            InfoTable(scroll, "Hardware Recommendations", [("", hw, C["dim"])], accent=C["accent"]).pack(fill="x", pady=(10, 10))

    # ────────────────────── AI CHAT ──────────────────────────────

    def _fill_chat(self):
        f = self.frames["chat"]
        for w in f.winfo_children(): w.destroy()

        ctk.CTkLabel(f, text="AI Assistant", font=("Segoe UI", 22, "bold"), text_color=C["text"]).pack(anchor="w", padx=20, pady=(16, 2))

        ai = InteractiveAI(api_key=self.api_key)
        status = "OpenAI GPT-4o-mini" if ai.available else "Offline mode (set API key for full AI)"
        clr = C["green"] if ai.available else C["yellow"]
        ctk.CTkLabel(f, text=status, font=("Segoe UI", 12), text_color=clr).pack(anchor="w", padx=20, pady=(0, 8))

        analyzer = AIAnalyzer(api_key=self.api_key)
        summary = analyzer._prepare_scan_summary(self.scan_results, self.all_issues, self.health_score)
        ai.set_context(summary, self.ai_analysis)
        self.ai_chat_inst = ai

        self._chat_box = ctk.CTkTextbox(f, fg_color=C["card"], text_color=C["text"], font=("Segoe UI", 13),
                                        corner_radius=12, border_width=1, border_color=C["border"], wrap="word")
        self._chat_box.pack(fill="both", expand=True, padx=20, pady=(0, 6))
        self._chat_box.insert("end", "AI Assistant ready! Ask anything about your PC.\n\nExamples:\n• Why is my CPU usage high?\n• How to speed up my PC?\n• Is my system secure?\n• What should I upgrade?\n\n")
        self._chat_box.configure(state="disabled")

        inp = ctk.CTkFrame(f, fg_color="transparent")
        inp.pack(fill="x", padx=20, pady=(0, 16))
        self._chat_entry = ctk.CTkEntry(inp, placeholder_text="Type your question...", font=("Segoe UI", 14),
                                        fg_color=C["bg2"], border_color=C["border"], height=42, corner_radius=10)
        self._chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._chat_entry.bind("<Return>", lambda e: self._send_msg())
        ctk.CTkButton(inp, text="Send", width=80, height=42, corner_radius=10, fg_color=C["accent"],
                      hover_color=C["accent2"], command=self._send_msg).pack(side="right")

    def _send_msg(self):
        msg = self._chat_entry.get().strip()
        if not msg: return
        self._chat_entry.delete(0, "end")
        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"\n{'─'*50}\nYou: {msg}\n\n")
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")
        threading.Thread(target=self._chat_reply, args=(msg,), daemon=True).start()

    def _chat_reply(self, msg):
        reply = self.ai_chat_inst.chat(msg)
        self.after(0, lambda: self._show_reply(reply))

    def _show_reply(self, reply):
        self._chat_box.configure(state="normal")
        self._chat_box.insert("end", f"AI: {reply}\n")
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")

    # ────────────────────── REPORT ───────────────────────────────

    def _export_report(self):
        if not self.scan_results:
            messagebox.showwarning("PC Doctor", "Run a scan first.")
            return
        gen = ReportGenerator()
        path = gen.generate(self.scan_results, self.all_issues, self.health_score, self.ai_analysis)
        if messagebox.askyesno("PC Doctor", f"Report saved:\n{path}\n\nOpen in browser?"):
            webbrowser.open(f"file:///{path}")


# ─── Entry ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = PCDoctorApp()
    app.mainloop()
