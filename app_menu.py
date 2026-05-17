"""
PC Doctor AI - Interactive Menu
Easy access to all features
"""

import os
import sys
import subprocess

os.environ['PYTHONIOENCODING'] = 'utf-8'
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from scanners import MasterScanner, SystemTools, AutoFixTools
from ai_engine import SmartDiagnostics, AICodeAssistant, test_ai_connection
from telegram_bot import TelegramNotifier, setup_telegram


def print_menu():
    print("\n" + "="*60)
    print("   🖥️  PC DOCTOR AI - MAIN MENU")
    print("="*60)
    print("""
  [1] 🔍 Full System Scan       - Run complete diagnostics
  [2] ⚡ Quick Scan              - Fast scan (skip event logs)
  [3] 📊 Background Monitor      - Real-time CPU/RAM/Disk
  [4] 📄 Generate HTML Report    - Save detailed report

  --- 🛠️ AUTO-FIX TOOLS ---
  [5] 🧹 Clean Temp Files        - Free up disk space
  [6] 🌐 Fix Network Issues      - Reset network settings
  [7] 🔧 Fix Windows Services    - Start stopped services
  [8] 🚀 Optimize Performance   - Speed up your PC

  --- 🤖 AI FEATURES ---
  [9] 💻 AI Fix Scripts         - Generate PowerShell fixes
  [10] 🧠 Smart Diagnostics     - AI-powered analysis
  [11] 🔗 Test AI Connection     - Check API keys

  --- 📱 OTHER ---
  [12] 📱 Telegram Setup        - Configure notifications
  [13] ⚙️ Open Settings         - Windows settings
  [14] 🚪 Exit

""" + "="*60)


def run_scan(quick=False):
    try:
        cmd = ["python", "main.py"]
        if quick:
            cmd.append("--quick")
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        print(f"Error: {e}")


def run_monitor():
    try:
        subprocess.run(["python", "main.py", "--monitor"], cwd=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        print(f"Error: {e}")


def clean_temp():
    print("\nCleaning temp files...")
    result = SystemTools.clean_temp_files()
    print(f"Cleaned: {result.get('cleaned_files')} files")
    print(f"Freed: {result.get('freed_mb')} MB")
    result2 = SystemTools.clear_recycle_bin()
    print("Recycle bin cleared")


def fix_network():
    print("\nFixing network...")
    result = AutoFixTools.fix_network()
    print(result.get("output", "Done"))


def fix_services():
    print("\nFixing services...")
    result = AutoFixTools.fix_services()
    print(result.get("output", "Done"))


def optimize():
    print("\nOptimizing performance...")
    result = AutoFixTools.optimize_performance()
    print(result.get("output", "Done"))


def ai_scripts():
    print("\n" + "="*40)
    print("   AI POWERShell FIX SCRIPTS")
    print("="*40)
    print("""
  [1] Temp Cleanup Script
  [2] Network Reset Script
  [3] Service Fix Script
  [4] Disk Check Script
  [5] Enable Antivirus
  [6] Enable Firewall
  [7] Windows Update
  [8] Driver Update
  [0] Back
""")

    choice = input("Select script: ").strip()

    scripts = {
        "1": "cleanup", "2": "network_reset", "3": "service_fix",
        "4": "disk_check", "5": "antivirus_enable", "6": "firewall_enable",
        "7": "update_windows", "8": "driver_update"
    }

    if choice in scripts:
        assistant = AICodeAssistant()
        script = assistant.generate_fix_script(scripts[choice])
        print("\n" + script)
        save = input("\nSave to file? (y/n): ").lower().strip()
        if save == "y":
            filename = f"fix_{scripts[choice]}.ps1"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(script)
            print(f"Saved to: {filename}")


def smart_diagnostics():
    print("\nRunning Smart Diagnostics...")
    scanner = MasterScanner()
    results = scanner.run_all_scans()

    sd = SmartDiagnostics()
    opt_report = sd.generate_optimization_report(results)

    print(f"\nTotal Recommendations: {opt_report['total_recommendations']}")
    print(f"Critical Issues: {opt_report['critical']}")

    for rec in opt_report['recommendations']:
        print(f"\n[{rec['category']}] {rec['issue']}")
        print(f"  Fix: {rec['fix']}")
        print(f"  Impact: {rec['impact']}")


def open_settings():
    print("\n" + "="*40)
    print("   QUICK SETTINGS ACCESS")
    print("="*40)
    print("""
  [1] Device Manager
  [2] Task Manager
  [3] Control Panel
  [4] Windows Settings
  [5] Disk Management
  [6] Services
  [7] Event Viewer
  [8] System Info
  [9] Power Options
  [0] Back
""")

    choice = input("Open: ").strip()

    tools = {
        "1": "devmgmt.msc", "2": "taskmgr", "3": "control",
        "4": "ms-settings:", "5": "diskmgmt.msc", "6": "services.msc",
        "7": "eventvwr.msc", "8": "msinfo32", "9": "powercfg.cpl"
    }

    if choice in tools:
        try:
            subprocess.Popen([tools[choice]])
            print("Opened!")
        except:
            print("Could not open")


def main():
    while True:
        print_menu()
        choice = input("Select option: ").strip()

        if choice == "1":
            run_scan(quick=False)
        elif choice == "2":
            run_scan(quick=True)
        elif choice == "3":
            run_monitor()
        elif choice == "4":
            run_scan(quick=False)
        elif choice == "5":
            clean_temp()
        elif choice == "6":
            fix_network()
        elif choice == "7":
            fix_services()
        elif choice == "8":
            optimize()
        elif choice == "9":
            ai_scripts()
        elif choice == "10":
            smart_diagnostics()
        elif choice == "11":
            test_ai_connection()
        elif choice == "12":
            setup_telegram()
        elif choice == "13":
            open_settings()
        elif choice == "14" or choice.lower() in ["exit", "q"]:
            print("\nGoodbye!")
            break
        else:
            print("Invalid option!")


if __name__ == "__main__":
    main()