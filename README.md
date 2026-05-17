# 🖥️ PC Doctor AI - Smart System Analyzer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Windows](https://img.shields.io/badge/Windows-10%2F11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

**AI-Powered PC Diagnostic & System Optimization Tool** 🇩🇿

*Comprehensive system analysis with intelligent AI diagnostics*

</div>

---

## ✨ Features

### 🔍 System Scanning (35+ Scanners)
| Category | Scanners |
|----------|----------|
| **Hardware** | CPU, Memory, Disk, GPU, Battery, Temperature |
| **Network** | Internet, WiFi, DNS, Firewall, IP Config |
| **Security** | Antivirus, Firewall, UAC, Windows Defender |
| **Software** | Programs, Drivers, Services, Startup Items |
| **Diagnostics** | Event Logs, Reliability, Windows Update, Registry |
| **Advanced** | Browser Cache, Disk Usage, Benchmark, Temp Files |

### 🤖 AI Features
- **Multi-AI Support**: OpenAI GPT, Claude, DeepSeek
- **Smart Diagnostics**: Predict future issues
- **Auto-Fix Scripts**: Generate PowerShell fix scripts
- **Interactive Chat**: Ask AI questions about your PC

### 🔧 Tools & Utilities
- Background real-time monitoring
- Auto-fix common issues
- HTML report generation
- Telegram notifications
- System optimization

---

## 🚀 Installation

### Prerequisites
```bash
Python 3.8+
```

### Option 1: Quick Install (Recommended)
```bash
# Just run the app - it will work!
python main.py --quick
```

### Option 2: With Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 3: Run Setup Script
```bash
python setup_venv.py
```

---

## 📖 Usage

### Basic Commands
```bash
# Full scan with terminal UI
python main.py

# Quick scan (skip event logs)
python main.py --quick

# Generate HTML report
python main.py --report

# Background monitor mode
python main.py --monitor

# Interactive AI chat
python main.py --chat
```

### With AI API Key
```bash
# OpenAI
python main.py --api-key sk-your-key

# Or set environment variable
set OPENAI_API_KEY=your-key
```

### Interactive Menu
```bash
python app_menu.py
```

---

## 📁 Project Structure

```
📦 PC-Doctor-AI
├── 📄 main.py              # Main application
├── 📄 scanners.py         # System scanners (35+)
├── 📄 ai_engine.py        # AI analysis engine
├── 📄 report_generator.py # HTML report generator
├── 📄 telegram_bot.py     # Telegram notifications
├── 📄 background_monitor.py # Real-time monitor
├── 📄 app_menu.py         # Interactive menu
├── 📄 setup_ai.py         # API key setup
├── 📄 requirements.txt    # Dependencies
└── 📄 README.md           # This file
```

---

## 🔧 Configuration

### API Keys Setup
```bash
# Run setup wizard
python setup_ai.py

# Or create config.ini manually:
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=ds-your-key
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=your-id
```

### Supported AI Providers
| Provider | Key Format | Model |
|----------|------------|-------|
| OpenAI | `sk-...` | GPT-4o Mini |
| Claude | `sk-ant...` | Claude 3 Haiku |
| DeepSeek | `ds-...` | DeepSeek Chat |

---

## 🎯 Quick Fix Commands

| Issue | Fix Command |
|-------|-------------|
| Slow PC | Run `python app_menu.py` → Option 8 |
| Full Disk | Option 5 → Clean Temp |
| Network | Option 6 → Fix Network |
| Services | Option 7 → Fix Services |

---

## 📊 Sample Output

```
╔══════════════════════════════════════════════════════╗
║   🖥️  PC Doctor AI - System Diagnostic             ║
╚══════════════════════════════════════════════════════╝

  📅 Date: 2026-05-17 14:30:00

────────────────── System Scan ───────────────────

✅ Health Score: 85/100 (Excellent)

🔴 Issues Found:
  • Real-Time Protection OFF
  • Disk C: 86% Full
  • 2 Driver Problems

💡 Recommendations:
  1. Enable Windows Defender
  2. Clean up disk space
  3. Update drivers
```

---

## 🛠️ Requirements

```
psutil          # System monitoring
rich            # Terminal UI
wmi             # Windows management
GPUtil          # GPU monitoring
openai          # OpenAI API
requests        # HTTP requests
```

---

## 📝 License

MIT License - Free to use and modify.

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**PC Doctor AI** - Built with ❤️ using Python

---

<div align="center">

*If you found this useful, please ⭐ the repo!*

</div>