# 💻 Pc-Doc-Ai — AI-Powered PC Diagnostic Tool — System analysis with 35+ scanners, auto-fix tools, and smart diagnostics for Windows

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/zougar99/Pc-Doc-Ai/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/zougar99/Pc-Doc-Ai?style=social)](https://github.com/zougar99/Pc-Doc-Ai)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-blue)](https://github.com/zougar99/Pc-Doc-Ai)

> AI-Powered PC Diagnostic Tool — System analysis with 35+ scanners, auto-fix tools, and smart diagnostics for Windows.

---

## 📖 Table of Contents
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [FAQ](#-faq)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features
- ✔ **35+ System Scanners** — Registry, disk, memory, network, startup, driver, security
- ✔ **AI Diagnosis** — ML model analyzes system health and suggests fixes
- ✔ **Auto-Fix** — One-click repair for common issues
- ✔ **Performance Optimization** — Clean temp files, optimize startup, defrag suggestions
- ✔ **Hardware Info** — Detailed report on CPU, GPU, RAM, motherboard, drives
- ✔ **Driver Scanner** — Find outdated or missing drivers
- ✔ **Report Export** — HTML / PDF diagnostic reports

---

## 🔮 How It Works

```
  Input ──► Processing Pipeline ──► Output
  ┌────────┐   ┌────────┐   ┌────────┐
  │ Data   │──►│ Engine │──►│ Result │
  │ Source │   │ Logic  │   │        │
  └────────┘   └────────┘   └────────┘
```

1. **Input** — Load data from file, API, or user input
2. **Process** — Core engine applies logic/analysis/transformation
3. **Output** — Results displayed in UI, saved to file, or sent via API

---

## 💻 Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| UI | CustomTkinter |
| AI | scikit-learn (local) |
| System | WMI + psutil + winreg |
| Platform | Windows |

---

## 🚀 Installation

```bash
git clone https://github.com/zougar99/Pc-Doc-Ai.git
cd Pc-Doc-Ai
pip install -r requirements.txt
```

---

## 📄 Configuration

Create a `config.yaml` or `.env` file in the project root:

```yaml
# Application settings
debug: false
port: 8080
theme: dark
language: en
```

---

## 🧰 Usage Guide

1. Run as Admin: `python main.py`
2. Click **Full Scan** for complete system analysis
3. Review issues by category
4. Click **Auto-Fix** to resolve
5. Export report

---

## 🖼 Screenshots

> *(Screenshots coming soon. PRs welcome!)*

---

## 🔄 Roadmap

- 🟢 Web dashboard
- 🟡 Mobile companion app
- ⚫ API access
- ⚫ Plugin system
- ⚫ Multi-language support

---

## ❓ FAQ

### Does it require internet?
No — all diagnostics run locally. Driver updates need internet.

### Is it safe?
Yes — all repairs are reversible. Auto-Fix creates restore points.

---

## 🚧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **App won't start** | Check Python version (3.10+); run `pip install -r requirements.txt` |
| **No output** | Check logs in `logs/` folder; enable debug mode in config |
| **Performance issues** | Close other applications; reduce batch size in config |
| **Dependency errors** | Create fresh venv: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📐 License
Distributed under the **MIT License**. See [`LICENSE`](https://github.com/zougar99/Pc-Doc-Ai/blob/main/LICENSE) for more information.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/zougar99">zougar99</a>
</p>
