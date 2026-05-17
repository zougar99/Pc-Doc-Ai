"""
PC Doctor AI - Smart System Analyzer
AI-Powered PC diagnostic and optimization tool.

Usage:
    python main.py              # Full scan with terminal UI
    python main.py --report     # Full scan + HTML report
    python main.py --chat       # Full scan + interactive AI chat
    python main.py --api-key YOUR_KEY   # Use OpenAI API key
    python main.py --monitor    # Background monitoring mode
    python main.py --monitor -i 5       # Monitor every 5 seconds
"""

import sys
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load config file if exists
CONFIG_FILE = "config.ini"
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                if key in ["OPENAI_API_KEY", "CLAUDE_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]:
                    os.environ[key] = value

import time
import argparse
import webbrowser
from datetime import datetime
import psutil

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

from scanners import MasterScanner, Issue
from ai_engine import AIAnalyzer, InteractiveAI
from report_generator import ReportGenerator


console = Console(force_terminal=True)

BANNER = """
[bold cyan]
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   PC DOCTOR AI - Smart System Analyzer                       ║
║                                                              ║
║   Comprehensive | AI-Powered | Fast                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]
"""

import sys
import os
import time
import argparse
import webbrowser
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

from scanners import MasterScanner, Issue
from ai_engine import AIAnalyzer, InteractiveAI
from report_generator import ReportGenerator


console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗  ██████╗    ██████╗  ██████╗  ██████╗             ║
║   ██╔══██╗██╔════╝    ██╔══██╗██╔═══██╗██╔════╝             ║
║   ██████╔╝██║         ██║  ██║██║   ██║██║                  ║
║   ██╔═══╝ ██║         ██║  ██║██║   ██║██║                  ║
║   ██║     ╚██████╗    ██████╔╝╚██████╔╝╚██████╗             ║
║   ╚═╝      ╚═════╝    ╚═════╝  ╚═════╝  ╚═════╝             ║
║                                                              ║
║              [bold white]PC Doctor AI - Smart System Analyzer[/bold white]        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝[/bold cyan]
"""


def display_banner():
    console.print(BANNER)
    console.print(f"  [dim]Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
    console.print()


def run_scan(scanner: MasterScanner) -> dict:
    """Run all system scans with a progress display."""
    results = {}

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning system...", total=len(scanner.scanners))

        scan_names = {
            "system": "📋 System Information",
            "cpu": "💻 CPU & Processor",
            "memory": "🧠 Memory / RAM",
            "disk": "💾 Storage & Disks",
            "network": "🌐 Network & Internet",
            "gpu": "🎮 Graphics / GPU",
            "processes": "⚙️ Running Processes",
            "security": "🔒 Security & Firewall",
            "battery": "🔋 Battery Status",
            "startup": "🚀 Startup Programs",
            "event_logs": "📝 Windows Event Logs",
            "installed_software": "📦 Installed Software",
            "drivers": "🎯 Drivers",
            "services": "🔧 Windows Services",
            "temp_files": "🗑️ Temp Files",
            "reliability": "📈 Windows Reliability",
            "windows_update": "🔄 Windows Update",
            "system_health": "❤️ System Health",
            "usb_devices": "🔌 USB Devices",
            "printers": "🖨️ Printers",
            "scheduled_tasks": "⏰ Scheduled Tasks",
            "firewall_rules": "🛡️ Firewall Rules",
            "dns_resolver": "🌍 DNS Resolver",
            "hosts_file": "📄 Hosts File",
            "network_shares": "📁 Network Shares",
            "registry": "🔐 Registry Health",
            "windows_features": "🎛️ Windows Features",
            "environment_vars": "⚡ Environment Variables",
            "ip_config": "🌍 IP Configuration",
            "error_summary": "⚠️ Error Summary",
            "benchmark": "🏆 System Benchmark",
            "disk_usage": "📊 Disk Usage Analysis",
            "browser_diagnostics": "🌐 Browser Diagnostics",
            "wifi_networks": "📶 WiFi Networks",
            "startup_performance": "🚀 Startup Performance",
        }

        for name, scan_obj in scanner.scanners.items():
            progress.update(task, description=f"Scanning {scan_names.get(name, name)}...")
            results[name] = scan_obj.scan()
            progress.advance(task)
            time.sleep(0.2)

    console.print()
    return results


def display_health_score(health_score: float):
    """Display the overall health score with a visual gauge."""
    if health_score >= 85:
        color, label = "green", "EXCELLENT"
    elif health_score >= 70:
        color, label = "yellow", "GOOD"
    elif health_score >= 50:
        color, label = "dark_orange", "FAIR"
    elif health_score >= 30:
        color, label = "red", "POOR"
    else:
        color, label = "bold red", "CRITICAL"

    bar_width = 40
    filled = int(health_score / 100 * bar_width)
    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (bar_width - filled)}[/dim]"

    score_panel = Panel(
        Text.from_markup(
            f"\n  {bar}  [{color}]{health_score:.0f}/100[/{color}]\n\n"
            f"  System Health: [{color}]{label}[/{color}]\n"
        ),
        title="[bold]Overall Health Score[/bold]",
        border_style=color,
        padding=(0, 2),
    )
    console.print(score_panel)


def display_system_info(results: dict):
    """Display system information summary."""
    sys_data = results.get("system")
    if not sys_data:
        return

    d = sys_data.data
    table = Table(
        title="System Information",
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
        pad_edge=True,
    )
    table.add_column("Property", style="cyan", width=22)
    table.add_column("Value", style="white")

    table.add_row("OS", d.get("os_name", d.get("os_edition", "N/A")))
    table.add_row("Build", d.get("build_number", d.get("os_version", "N/A")))
    table.add_row("Hostname", d.get("hostname", "N/A"))
    table.add_row("Architecture", d.get("architecture", "N/A"))
    table.add_row("Uptime", d.get("uptime_human", "N/A"))
    table.add_row("Motherboard", f"{d.get('motherboard_manufacturer', '')} {d.get('motherboard', 'N/A')}")
    table.add_row("BIOS", f"{d.get('bios_manufacturer', '')} {d.get('bios_version', 'N/A')}")

    console.print(table)
    console.print()


def display_hardware_summary(results: dict):
    """Display CPU, Memory, Disk summary in a compact view."""
    tables = []

    cpu = results.get("cpu")
    if cpu:
        d = cpu.data
        t = Table(title="CPU", box=box.SIMPLE_HEAVY, border_style="cyan", show_header=False)
        t.add_column("", style="dim", width=14)
        t.add_column("", style="white")
        t.add_row("Processor", str(d.get("processor", "N/A"))[:40])
        t.add_row("Cores", f"{d.get('physical_cores', '?')}P / {d.get('logical_cores', '?')}L")
        t.add_row("Frequency", f"{d.get('current_frequency_mhz', 'N/A')} MHz")
        usage = d.get("average_usage_percent", 0)
        color = "red" if usage > 80 else "yellow" if usage > 50 else "green"
        t.add_row("Usage", f"[{color}]{usage}%[/{color}]")
        temp = d.get("temperature_celsius")
        if temp:
            tc = "red" if temp > 80 else "yellow" if temp > 65 else "green"
            t.add_row("Temperature", f"[{tc}]{temp}°C[/{tc}]")
        tables.append(t)

    mem = results.get("memory")
    if mem:
        d = mem.data
        t = Table(title="Memory", box=box.SIMPLE_HEAVY, border_style="magenta", show_header=False)
        t.add_column("", style="dim", width=14)
        t.add_column("", style="white")
        t.add_row("Total", f"{d.get('total_gb', 'N/A')} GB")
        t.add_row("Used", f"{d.get('used_gb', 'N/A')} GB")
        t.add_row("Available", f"{d.get('available_gb', 'N/A')} GB")
        pct = d.get("usage_percent", 0)
        color = "red" if pct > 85 else "yellow" if pct > 65 else "green"
        t.add_row("Usage", f"[{color}]{pct}%[/{color}]")
        t.add_row("Swap", f"{d.get('swap_used_gb', 'N/A')} / {d.get('swap_total_gb', 'N/A')} GB")
        tables.append(t)

    if tables:
        console.print(Columns(tables, padding=(0, 3)))
        console.print()

    disk = results.get("disk")
    if disk:
        dt = Table(title="Storage", box=box.ROUNDED, border_style="green")
        dt.add_column("Drive", style="cyan")
        dt.add_column("Type", style="dim")
        dt.add_column("Total", justify="right")
        dt.add_column("Used", justify="right")
        dt.add_column("Free", justify="right")
        dt.add_column("Usage", justify="right")
        for part in disk.data.get("partitions", []):
            pct = part.get("usage_percent", 0)
            color = "red" if pct > 90 else "yellow" if pct > 75 else "green"
            dt.add_row(
                part.get("mountpoint", "?"),
                part.get("filesystem", "?"),
                f"{part.get('total_gb', '?')} GB",
                f"{part.get('used_gb', '?')} GB",
                f"{part.get('free_gb', '?')} GB",
                f"[{color}]{pct}%[/{color}]",
            )
        console.print(dt)
        console.print()


def display_network_info(results: dict):
    """Display network information."""
    net = results.get("network")
    if not net:
        return

    d = net.data
    connected = d.get("internet_connected", False)
    dns = d.get("dns_working", False)

    status = "[green]Connected[/green]" if connected else "[red]Disconnected[/red]"
    dns_status = "[green]Working[/green]" if dns else "[red]Failed[/red]"
    latency = d.get("latency_ms", "N/A")

    panel = Panel(
        Text.from_markup(
            f"  Internet: {status}  |  DNS: {dns_status}  |  Latency: {latency} ms\n"
            f"  Data Sent: {d.get('bytes_sent_gb', 'N/A')} GB  |  Received: {d.get('bytes_recv_gb', 'N/A')} GB"
        ),
        title="[bold]Network Status[/bold]",
        border_style="blue",
    )
    console.print(panel)
    console.print()


def display_gpu_info(results: dict):
    """Display GPU information."""
    gpu = results.get("gpu")
    if not gpu or not gpu.data.get("gpus"):
        return

    for g in gpu.data["gpus"]:
        table = Table(title=f"GPU: {g.get('name', 'Unknown')}", box=box.SIMPLE_HEAVY, border_style="yellow", show_header=False)
        table.add_column("", style="dim", width=16)
        table.add_column("", style="white")
        if g.get("memory_total_mb"):
            table.add_row("VRAM", f"{g.get('memory_used_mb', 0):.0f} / {g.get('memory_total_mb', 0):.0f} MB")
            table.add_row("VRAM Usage", f"{g.get('memory_usage_percent', 0)}%")
            table.add_row("GPU Load", f"{g.get('gpu_usage_percent', 0)}%")
        if g.get("temperature_celsius"):
            tc = "red" if g["temperature_celsius"] > 85 else "yellow" if g["temperature_celsius"] > 70 else "green"
            table.add_row("Temperature", f"[{tc}]{g['temperature_celsius']}°C[/{tc}]")
        if g.get("driver_version"):
            table.add_row("Driver", str(g["driver_version"]))
        if g.get("video_memory_mb"):
            table.add_row("Video Memory", f"{g['video_memory_mb']:.0f} MB")
        if g.get("status"):
            table.add_row("Status", g["status"])
        console.print(table)
    console.print()


def display_security_info(results: dict):
    """Display security status."""
    sec = results.get("security")
    if not sec:
        return

    d = sec.data
    fw = "[green]Enabled[/green]" if d.get("firewall_enabled") else "[red]DISABLED[/red]"
    defender_data = d.get("windows_defender", {})
    if isinstance(defender_data, dict):
        av = "[green]Active[/green]" if defender_data.get("enabled") else "[red]DISABLED[/red]"
        rt = "[green]Active[/green]" if defender_data.get("realtime_protection") else "[red]OFF[/red]"
    else:
        av, rt = "[dim]Unknown[/dim]", "[dim]Unknown[/dim]"
    uac = "[green]Enabled[/green]" if d.get("uac_enabled") else "[red]Disabled[/red]"

    panel = Panel(
        Text.from_markup(
            f"  Firewall: {fw}  |  Antivirus: {av}\n"
            f"  Real-time Protection: {rt}  |  UAC: {uac}"
        ),
        title="[bold]Security Status[/bold]",
        border_style="red" if not d.get("firewall_enabled") else "green",
    )
    console.print(panel)
    console.print()


def display_top_processes(results: dict):
    """Display top resource-consuming processes."""
    proc = results.get("processes")
    if not proc:
        return

    d = proc.data
    table = Table(title=f"Top Processes ({d.get('total_processes', '?')} total)", box=box.ROUNDED, border_style="cyan")
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Process Name", style="white")
    table.add_column("CPU %", justify="right")
    table.add_column("RAM %", justify="right")

    seen = set()
    combined = {}
    for p in d.get("top_cpu_consumers", []):
        combined[p["pid"]] = {"pid": p["pid"], "name": p["name"], "cpu": p["cpu_percent"], "mem": 0}
    for p in d.get("top_memory_consumers", []):
        if p["pid"] in combined:
            combined[p["pid"]]["mem"] = p["memory_percent"]
        else:
            combined[p["pid"]] = {"pid": p["pid"], "name": p["name"], "cpu": 0, "mem": p["memory_percent"]}

    sorted_procs = sorted(combined.values(), key=lambda x: x["cpu"] + x["mem"], reverse=True)[:10]
    for p in sorted_procs:
        cpu_c = "red" if p["cpu"] > 50 else "yellow" if p["cpu"] > 20 else "green"
        mem_c = "red" if p["mem"] > 15 else "yellow" if p["mem"] > 5 else "green"
        table.add_row(
            str(p["pid"]),
            p["name"][:30],
            f"[{cpu_c}]{p['cpu']:.1f}%[/{cpu_c}]",
            f"[{mem_c}]{p['mem']:.1f}%[/{mem_c}]",
        )

    console.print(table)
    console.print()


def display_issues(issues: list):
    """Display all detected issues organized by severity."""
    if not issues:
        console.print(Panel(
            "[bold green]No issues detected! Your system appears healthy.[/bold green]",
            title="Issues", border_style="green",
        ))
        console.print()
        return

    critical = [i for i in issues if i.severity == "critical"]
    warnings = [i for i in issues if i.severity == "warning"]
    infos = [i for i in issues if i.severity == "info"]

    tree = Tree("[bold]Detected Issues[/bold]")

    if critical:
        crit_branch = tree.add(f"[bold red]CRITICAL ({len(critical)})[/bold red]")
        for i in critical:
            node = crit_branch.add(f"[red]{i.title}[/red] [{i.category}]")
            node.add(f"[dim]{i.description}[/dim]")
            node.add(f"[green]Fix: {i.recommendation}[/green]")

    if warnings:
        warn_branch = tree.add(f"[bold yellow]WARNINGS ({len(warnings)})[/bold yellow]")
        for i in warnings:
            node = warn_branch.add(f"[yellow]{i.title}[/yellow] [{i.category}]")
            node.add(f"[dim]{i.description}[/dim]")
            node.add(f"[green]Fix: {i.recommendation}[/green]")

    if infos:
        info_branch = tree.add(f"[bold blue]INFO ({len(infos)})[/bold blue]")
        for i in infos:
            node = info_branch.add(f"[blue]{i.title}[/blue] [{i.category}]")
            node.add(f"[dim]{i.description}[/dim]")

    console.print(Panel(tree, border_style="bright_white"))
    console.print()


def display_ai_analysis(analysis: dict):
    """Display AI analysis results."""
    console.print(Rule("[bold magenta]AI Analysis[/bold magenta]"))
    console.print()

    analysis_type = analysis.get("analysis_type", "Unknown")
    console.print(f"  [dim]Engine: {analysis_type}[/dim]")
    console.print()

    console.print(Panel(
        analysis.get("overall_assessment", "No assessment available."),
        title=f"[bold]Assessment - {analysis.get('health_rating', 'Unknown')}[/bold]",
        border_style="magenta",
        padding=(1, 2),
    ))

    crit_issues = analysis.get("critical_issues", [])
    if crit_issues:
        console.print()
        table = Table(title="Priority Issues & Solutions", box=box.ROUNDED, border_style="red")
        table.add_column("Priority", style="bold", width=10)
        table.add_column("Issue", style="white", width=25)
        table.add_column("Impact", style="yellow", width=30)
        table.add_column("Solution", style="green", width=35)

        for item in crit_issues:
            p = item.get("priority", "medium")
            pc = "red" if p == "immediate" else "yellow" if p == "high" else "cyan"
            table.add_row(
                f"[{pc}]{p.upper()}[/{pc}]",
                item.get("issue", ""),
                item.get("impact", "")[:80],
                item.get("solution", "")[:80],
            )
        console.print(table)

    tips = analysis.get("optimization_tips", [])
    if tips:
        console.print()
        console.print("[bold cyan]Optimization Tips:[/bold cyan]")
        for tip in tips:
            console.print(f"  [magenta]{tip.get('area', '')}:[/magenta] {tip.get('tip', '')}")
            console.print(f"    [dim green]Expected: {tip.get('expected_improvement', '')}[/dim green]")

    hw = analysis.get("hardware_recommendations")
    if hw:
        console.print()
        console.print(Panel(hw, title="[bold]Hardware Recommendations[/bold]", border_style="cyan"))

    console.print()


def interactive_chat(ai_chat: InteractiveAI, scan_results: dict, analysis: dict):
    """Run interactive AI chat mode."""
    console.print(Rule("[bold green]Interactive AI Assistant[/bold green]"))
    console.print()

    if ai_chat.available:
        console.print("[green]AI assistant is ready (using OpenAI GPT-4o-mini)[/green]")
    else:
        console.print("[yellow]Running in offline mode (basic responses). Set OPENAI_API_KEY for full AI.[/yellow]")

    console.print("[dim]Type your questions about your PC. Type 'exit' or 'quit' to stop.[/dim]")
    console.print()

    analyzer = AIAnalyzer()
    summary = analyzer._prepare_scan_summary(scan_results, [], 0)
    ai_chat.set_context(summary, analysis)

    while True:
        try:
            question = Prompt.ask("[bold cyan]You[/bold cyan]")
            if not question or question.lower() in ("exit", "quit", "q", "bye"):
                console.print("[dim]Goodbye![/dim]")
                break

            with console.status("[bold magenta]AI is thinking...[/bold magenta]"):
                response = ai_chat.chat(question)

            console.print()
            console.print(Panel(response, title="[bold magenta]AI Assistant[/bold magenta]", border_style="magenta", padding=(1, 2)))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Chat ended.[/dim]")
            break
        except EOFError:
            break


def run_monitor_mode(interval=5):
    console.print(Panel.fit("[bold cyan]PC DIAGNOSTIC - BACKGROUND MONITOR[/bold cyan]\n"
                           "[dim]Press Ctrl+C to stop[/dim]", border_style="cyan"))
    console.print(f"\n[green]Monitoring every {interval} seconds...[/green]\n")

    alert_count = 0
    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('C:')

            cpu_color = "green" if cpu < 60 else "yellow" if cpu < 80 else "red"
            mem_color = "green" if mem.percent < 60 else "yellow" if mem.percent < 80 else "red"
            disk_color = "green" if disk.percent < 70 else "yellow" if disk.percent < 85 else "red"

            console.print(f"[{datetime.now().strftime('%H:%M:%S')}] ", end="")
            console.print(f"CPU: [{cpu_color}]{cpu:.1f}%[/{cpu_color}] ", end="")
            console.print(f"MEM: [{mem_color}]{mem.percent:.1f}%[/{mem_color}] ", end="")
            console.print(f"DISK: [{disk_color}]{disk.percent:.1f}%[/{disk_color}]")

            if cpu > 90:
                console.print("[red]ALERT: CPU Critical![/red]")
                alert_count += 1
            if mem.percent > 90:
                console.print("[red]ALERT: Memory Critical![/red]")
                alert_count += 1
            if disk.percent > 95:
                console.print("[red]ALERT: Disk Critical![/red]")
                alert_count += 1

            time.sleep(interval - 1)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Monitor stopped. Total alerts: {alert_count}[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="PC Doctor AI - Smart System Analyzer")
    parser.add_argument("--api-key", type=str, help="OpenAI API key for AI analysis")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--chat", action="store_true", help="Start interactive AI chat after scan")
    parser.add_argument("--quick", action="store_true", help="Quick scan (skip event logs)")
    parser.add_argument("--monitor", action="store_true", help="Run background monitor mode")
    parser.add_argument("--interval", type=int, default=2, help="Monitor interval in seconds")
    args = parser.parse_args()

    if args.monitor:
        run_monitor_mode(args.interval)
        return

    display_banner()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")

    if api_key:
        console.print("[green]  OpenAI API key detected - AI analysis enabled[/green]")
    else:
        console.print("[yellow]  No OpenAI API key - using built-in analysis[/yellow]")
        console.print("[dim]  Set OPENAI_API_KEY or use --api-key for AI-powered analysis[/dim]")
    console.print()

    # ── Run Scans ────────────────────────────────────────────────
    console.print(Rule("[bold]Starting System Scan[/bold]"))
    console.print()

    scanner = MasterScanner()
    if args.quick:
        del scanner.scanners["event_logs"]

    results = run_scan(scanner)
    health_score = scanner.calculate_overall_health(results)
    all_issues = scanner.get_all_issues(results)

    console.print("[bold green]Scan complete![/bold green]")
    console.print()

    # ── Display Results ──────────────────────────────────────────
    display_health_score(health_score)
    console.print()
    display_system_info(results)
    display_hardware_summary(results)
    display_network_info(results)
    display_gpu_info(results)
    display_security_info(results)
    display_top_processes(results)
    display_issues(all_issues)

    # ── AI Analysis ──────────────────────────────────────────────
    console.print(Rule("[bold]Running AI Analysis[/bold]"))
    console.print()

    with console.status("[bold magenta]AI is analyzing your system...[/bold magenta]"):
        ai_analyzer = AIAnalyzer(api_key=api_key)
        analysis = ai_analyzer.analyze(results, all_issues, health_score)

    display_ai_analysis(analysis)

    # ── Generate Report ──────────────────────────────────────────
    if args.report:
        console.print(Rule("[bold]Generating Report[/bold]"))
        with console.status("[bold blue]Creating HTML report...[/bold blue]"):
            report_gen = ReportGenerator()
            report_path = report_gen.generate(results, all_issues, health_score, analysis)
        console.print(f"[bold green]Report saved:[/bold green] {report_path}")
        if Confirm.ask("Open report in browser?", default=True):
            webbrowser.open(f"file:///{report_path}")
        console.print()

    # ── Interactive Chat ─────────────────────────────────────────
    if args.chat:
        ai_chat = InteractiveAI(api_key=api_key)
        interactive_chat(ai_chat, results, analysis)
    elif not args.report:
        console.print()
        console.print("[dim]Tip: Run with --report for HTML report, --chat for AI assistant[/dim]")

    console.print()
    console.print(Rule("[bold cyan]Scan Complete[/bold cyan]"))
    console.print()


if __name__ == "__main__":
    main()
