"""
AI Analysis Engine - Provides intelligent PC diagnostics using OpenAI API
with a built-in rule-based fallback when no API key is configured.

Enhanced with:
- Interactive chatbot mode
- System optimization suggestions
- Natural language issue explanations
- Step-by-step fix guides
"""

import json
import os
import time
from typing import Optional, List, Dict
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIAnalyzer:
    """Analyzes scan results using AI (OpenAI) or rule-based fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    @property
    def ai_available(self) -> bool:
        return self.client is not None

    def analyze(self, scan_results: dict, issues: list, health_score: float) -> dict:
        """Run AI or rule-based analysis on scan results."""
        if self.ai_available:
            try:
                return self._ai_analysis(scan_results, issues, health_score)
            except Exception as e:
                return self._rule_based_analysis(scan_results, issues, health_score, ai_error=str(e))
        return self._rule_based_analysis(scan_results, issues, health_score)

    def _ai_analysis(self, scan_results: dict, issues: list, health_score: float) -> dict:
        scan_summary = self._prepare_scan_summary(scan_results, issues, health_score)

        system_prompt = """You are an expert PC diagnostics engineer and system administrator.
You analyze system scan data and provide detailed, actionable diagnostics.

Your response MUST be valid JSON with this exact structure:
{
    "overall_assessment": "A comprehensive paragraph about the system's health",
    "health_rating": "Excellent/Good/Fair/Poor/Critical",
    "critical_issues": [
        {
            "issue": "Issue title",
            "explanation": "Detailed explanation of the problem",
            "impact": "What happens if not fixed",
            "solution": "Step-by-step solution",
            "priority": "immediate/high/medium/low"
        }
    ],
    "optimization_tips": [
        {
            "area": "Category",
            "tip": "Specific optimization tip",
            "expected_improvement": "What will improve"
        }
    ],
    "hardware_recommendations": "Paragraph about potential hardware upgrades if needed",
    "maintenance_schedule": "Recommended maintenance tasks and frequency"
}

Be specific, technical but understandable, and practical in your recommendations."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this PC diagnostic data:\n\n{scan_summary}"}
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        result["analysis_type"] = "AI-Powered (GPT-4o-mini)"
        return result

    def _prepare_scan_summary(self, scan_results: dict, issues: list, health_score: float) -> str:
        summary = f"OVERALL HEALTH SCORE: {health_score:.1f}/100\n\n"

        for name, result in scan_results.items():
            summary += f"=== {result.category.upper()} ===\n"
            for key, value in result.data.items():
                if isinstance(value, (list, dict)):
                    summary += f"  {key}: {json.dumps(value, default=str)[:300]}\n"
                else:
                    summary += f"  {key}: {value}\n"
            summary += "\n"

        if issues:
            summary += "=== DETECTED ISSUES ===\n"
            for issue in issues:
                summary += f"  [{issue.severity.upper()}] {issue.title}: {issue.description}\n"

        return summary

    def _rule_based_analysis(self, scan_results: dict, issues: list, health_score: float, ai_error: str = None) -> dict:
        """Intelligent rule-based analysis when AI is not available."""
        critical = [i for i in issues if i.severity == "critical"]
        warnings = [i for i in issues if i.severity == "warning"]
        infos = [i for i in issues if i.severity == "info"]

        if health_score >= 85:
            rating = "Excellent"
        elif health_score >= 70:
            rating = "Good"
        elif health_score >= 50:
            rating = "Fair"
        elif health_score >= 30:
            rating = "Poor"
        else:
            rating = "Critical"

        assessment = self._build_assessment(scan_results, critical, warnings, health_score, rating)
        critical_issues = self._build_critical_issues(critical, warnings)
        optimization_tips = self._build_optimization_tips(scan_results, issues)
        hardware_recs = self._build_hardware_recommendations(scan_results)
        maintenance = self._build_maintenance_schedule(issues)

        result = {
            "analysis_type": "Rule-Based Analysis (Local)",
            "overall_assessment": assessment,
            "health_rating": rating,
            "critical_issues": critical_issues,
            "optimization_tips": optimization_tips,
            "hardware_recommendations": hardware_recs,
            "maintenance_schedule": maintenance,
        }

        if ai_error:
            result["ai_note"] = f"AI analysis failed ({ai_error}). Using built-in analysis."

        return result

    def _build_assessment(self, results, critical, warnings, score, rating):
        parts = [f"System health is rated '{rating}' with a score of {score:.0f}/100."]

        if critical:
            parts.append(f"There are {len(critical)} critical issue(s) that need immediate attention.")
        if warnings:
            parts.append(f"Found {len(warnings)} warning(s) that should be addressed.")

        sys_data = results.get("system", None)
        if sys_data and sys_data.data.get("os_name"):
            parts.append(f"Running {sys_data.data['os_name']}.")

        mem_data = results.get("memory", None)
        if mem_data:
            parts.append(f"System has {mem_data.data.get('total_gb', '?')}GB RAM with {mem_data.data.get('usage_percent', '?')}% usage.")

        cpu_data = results.get("cpu", None)
        if cpu_data:
            parts.append(f"CPU has {cpu_data.data.get('logical_cores', '?')} logical cores at {cpu_data.data.get('average_usage_percent', '?')}% average load.")

        if not critical and not warnings:
            parts.append("Your system appears to be in healthy condition. Keep up with regular maintenance.")

        return " ".join(parts)

    def _build_critical_issues(self, critical, warnings):
        issues_list = []
        for issue in critical:
            issues_list.append({
                "issue": issue.title,
                "explanation": issue.description,
                "impact": self._get_impact(issue),
                "solution": issue.recommendation,
                "priority": "immediate"
            })
        for issue in warnings[:5]:
            issues_list.append({
                "issue": issue.title,
                "explanation": issue.description,
                "impact": self._get_impact(issue),
                "solution": issue.recommendation,
                "priority": "high" if "critical" in issue.description.lower() else "medium"
            })
        return issues_list

    def _get_impact(self, issue):
        impact_map = {
            "CPU": "System slowdowns, application freezing, potential hardware damage from overheating.",
            "Memory": "Application crashes, system freezing, poor multitasking performance.",
            "Disk": "Unable to save files, system crashes, data corruption risk.",
            "Network": "No internet access, slow downloads, connection drops.",
            "GPU": "Graphics artifacts, gaming/rendering issues, potential hardware failure.",
            "Security": "Vulnerability to malware, data theft, unauthorized access.",
            "Battery": "Unexpected shutdowns, data loss.",
            "Processes": "System slowdown, unresponsive applications.",
        }
        return impact_map.get(issue.category, "May affect system stability and performance.")

    def _build_optimization_tips(self, results, issues):
        tips = []

        mem = results.get("memory")
        if mem and mem.data.get("usage_percent", 0) > 60:
            tips.append({
                "area": "Memory",
                "tip": "Close browser tabs you're not using. Each tab consumes significant RAM.",
                "expected_improvement": "10-30% memory reduction"
            })

        disk = results.get("disk")
        if disk:
            for part in disk.data.get("partitions", []):
                if part.get("usage_percent", 0) > 70:
                    tips.append({
                        "area": "Disk",
                        "tip": f"Run Disk Cleanup on {part['mountpoint']}. Clear temp files, browser cache, and recycle bin.",
                        "expected_improvement": "2-10GB space recovery"
                    })
                    break

        startup = results.get("startup")
        if startup and startup.data.get("count", 0) > 5:
            tips.append({
                "area": "Boot Speed",
                "tip": "Disable unnecessary startup programs via Task Manager > Startup tab.",
                "expected_improvement": "30-60% faster boot time"
            })

        cpu = results.get("cpu")
        if cpu and cpu.data.get("average_usage_percent", 0) > 50:
            tips.append({
                "area": "CPU",
                "tip": "Check for background updates, antivirus scans, or indexing services running during work hours.",
                "expected_improvement": "Smoother overall performance"
            })

        tips.append({
            "area": "General",
            "tip": "Keep Windows and drivers up to date. Run 'sfc /scannow' in admin Command Prompt to check system files.",
            "expected_improvement": "Better stability and security"
        })

        tips.append({
            "area": "Performance",
            "tip": "Set Windows power plan to 'High Performance' for maximum speed (uses more energy).",
            "expected_improvement": "5-15% performance boost"
        })

        return tips

    def _build_hardware_recommendations(self, results):
        recs = []

        mem = results.get("memory")
        if mem:
            total_gb = mem.data.get("total_gb", 0)
            if total_gb < 8:
                recs.append(f"Upgrade RAM from {total_gb}GB to at least 16GB for significantly better multitasking.")
            elif total_gb < 16 and mem.data.get("usage_percent", 0) > 70:
                recs.append("Consider upgrading to 16GB or 32GB RAM given your current memory usage patterns.")

        disk = results.get("disk")
        if disk:
            for part in disk.data.get("partitions", []):
                if part.get("filesystem") != "NTFS":
                    continue
                if part.get("total_gb", 0) < 256:
                    recs.append(f"Consider upgrading to a larger SSD (500GB+) for drive {part['mountpoint']}.")

        if not recs:
            recs.append("No urgent hardware upgrades needed at this time. System hardware is adequate for current usage.")

        return " ".join(recs)

    def _build_maintenance_schedule(self, issues):
        tasks = [
            "Weekly: Run Disk Cleanup and check for Windows updates.",
            "Monthly: Review startup programs, clear browser cache, run full antivirus scan.",
            "Quarterly: Check for driver updates, clean dust from hardware (desktop), review installed programs.",
            "Yearly: Consider clean Windows install if system becomes slow, check hardware health.",
        ]
        if any(i.category == "Security" for i in issues):
            tasks.insert(0, "IMMEDIATELY: Address security issues found in this scan.")
        return " | ".join(tasks)


class InteractiveAI:
    """Interactive AI chat for follow-up questions about PC diagnostics."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        self.conversation_history = []
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    @property
    def available(self) -> bool:
        return self.client is not None

    def set_context(self, scan_summary: str, analysis: dict):
        """Set the diagnostic context for the conversation."""
        context = f"""You are a PC diagnostics AI assistant. You have just analyzed a computer and found these results:

SCAN RESULTS:
{scan_summary}

ANALYSIS:
{json.dumps(analysis, indent=2, default=str)}

Help the user understand their PC issues, answer questions about the diagnostics,
and provide step-by-step guidance for fixing problems. Be friendly, clear, and technical when needed.
If asked about something outside PC diagnostics, politely redirect to PC-related topics."""

        self.conversation_history = [{"role": "system", "content": context}]

    def chat(self, user_message: str) -> str:
        """Send a message and get AI response."""
        if not self.available:
            return self._offline_response(user_message)

        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.conversation_history,
                temperature=0.5,
                max_tokens=1000,
            )
            reply = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": reply})

            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[:1] + self.conversation_history[-18:]

            return reply
        except Exception as e:
            return f"AI Error: {e}\n\nPlease check your API key or internet connection."

    def _offline_response(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["cpu", "processor"]):
            return ("For CPU issues:\n"
                    "1. Open Task Manager (Ctrl+Shift+Esc)\n"
                    "2. Click 'CPU' column to sort by usage\n"
                    "3. Right-click high-usage processes > End Task\n"
                    "4. Check for malware with a full antivirus scan\n"
                    "5. Clean dust from CPU cooler if temperature is high")
        elif any(w in msg for w in ["memory", "ram"]):
            return ("For memory issues:\n"
                    "1. Close unnecessary browser tabs and applications\n"
                    "2. Disable startup programs (Task Manager > Startup)\n"
                    "3. Check for memory leaks in applications\n"
                    "4. Consider upgrading RAM if consistently above 80%")
        elif any(w in msg for w in ["disk", "storage", "space"]):
            return ("For disk space issues:\n"
                    "1. Run Disk Cleanup (search 'Disk Cleanup' in Start)\n"
                    "2. Clear browser cache and temp files\n"
                    "3. Uninstall programs you don't use\n"
                    "4. Move large files to external storage\n"
                    "5. Empty the Recycle Bin")
        elif any(w in msg for w in ["network", "internet", "wifi"]):
            return ("For network issues:\n"
                    "1. Restart your router/modem\n"
                    "2. Run 'ipconfig /flushdns' in Command Prompt\n"
                    "3. Try changing DNS to 8.8.8.8\n"
                    "4. Update network adapter drivers\n"
                    "5. Check for VPN interference")
        elif any(w in msg for w in ["slow", "performance", "speed"]):
            return ("To improve performance:\n"
                    "1. Disable unnecessary startup programs\n"
                    "2. Run Disk Cleanup and defragmentation\n"
                    "3. Set power plan to 'High Performance'\n"
                    "4. Run 'sfc /scannow' as administrator\n"
                    "5. Check for malware\n"
                    "6. Consider upgrading to SSD if using HDD")
        elif any(w in msg for w in ["security", "virus", "malware"]):
            return ("For security concerns:\n"
                    "1. Run full Windows Defender scan\n"
                    "2. Enable Windows Firewall\n"
                    "3. Keep Windows updated\n"
                    "4. Enable UAC (User Account Control)\n"
                    "5. Use strong passwords and enable 2FA\n"
                    "6. Consider using Malwarebytes for additional scanning")
        else:
            return ("I can help with these PC topics:\n"
                    "- CPU / processor issues\n"
                    "- Memory / RAM problems\n"
                    "- Disk / storage management\n"
                    "- Network / internet issues\n"
                    "- Performance optimization\n"
                    "- Security concerns\n\n"
                    "For AI-powered detailed answers, set your OpenAI API key:\n"
                    "  set OPENAI_API_KEY=your-key-here")


class SmartDiagnostics:
    """AI-powered smart diagnostics with detailed fix guides."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    def generate_fix_guide(self, issue: dict, scan_data: dict) -> dict:
        """Generate a step-by-step fix guide for a specific issue."""
        category = issue.get("category", "")
        title = issue.get("title", "")
        severity = issue.get("severity", "")

        guides = {
            "Memory": {
                "high_ram": [
                    "1. Open Task Manager (Ctrl+Shift+Esc)",
                    "2. Click Memory column to sort",
                    "3. Right-click unused apps > End task",
                    "4. Disable startup programs in Startup tab",
                    "5. Consider adding more RAM"
                ],
                "low_ram": [
                    "1. Close all unnecessary applications",
                    "2. Right-click taskbar > Start Task Manager",
                    "3. End processes not needed for Windows",
                    "4. Restart your PC to clear memory",
                    "5. Consider upgrading to at least 8GB RAM"
                ]
            },
            "Disk": {
                "full": [
                    "1. Open Settings > Storage",
                    "2. Click 'Cleanup recommendations'",
                    "3. Select 'Temporary files' and delete",
                    "4. Uninstall unused programs",
                    "5. Move large files to another drive",
                    "6. Empty Recycle Bin"
                ]
            },
            "Security": {
                "real_time_protection": [
                    "1. Open Windows Security (Win key + I)",
                    "2. Go to Virus & threat protection",
                    "3. Click 'Manage settings'",
                    "4. Turn ON Real-time protection",
                    "5. Also enable Cloud-delivered protection"
                ]
            },
            "Network": {
                "no_internet": [
                    "1. Restart your router/modem",
                    "2. Run 'ipconfig /release' then 'ipconfig /renew'",
                    "3. Run 'ipconfig /flushdns'",
                    "4. Check cable/fiber connections",
                    "5. Try Google DNS (8.8.8.8)"
                ]
            },
            "CPU": {
                "high": [
                    "1. Open Task Manager",
                    "2. Sort by CPU usage",
                    "3. End suspicious processes",
                    "4. Run full antivirus scan",
                    "5. Check for cryptocurrency miners"
                ]
            }
        }

        guide = guides.get(category, {}).get(title.lower().replace(" ", "_"), [
            "1. Search for solution online",
            "2. Check Windows Event Viewer",
            "3. Run system file checker (sfc /scannow)",
            "4. Consider restarting PC"
        ])

        return {
            "issue": title,
            "severity": severity,
            "steps": guide,
            "estimated_time": "5-15 minutes",
            "difficulty": "Easy" if severity == "info" else "Medium"
        }

    def predict_issues(self, scan_data: dict) -> List[dict]:
        """Predict potential future issues based on trends."""
        predictions = []

        disk = scan_data.get("disk", {})
        if disk.get("data", {}).get("partitions"):
            for part in disk["data"]["partitions"]:
                if part.get("usage_percent", 0) > 80:
                    predictions.append({
                        "type": "disk_full",
                        "likelihood": "High",
                        "timeline": "2-4 weeks",
                        "recommendation": "Free up disk space now to prevent issues"
                    })

        mem = scan_data.get("memory", {})
        if mem.get("health_score", 100) < 80:
            predictions.append({
                "type": "memory_issues",
                "likelihood": "Medium",
                "timeline": "1-2 months",
                "recommendation": "Consider upgrading RAM soon"
            })

        return predictions

    def generate_optimization_report(self, scan_data: dict) -> dict:
        """Generate system optimization recommendations."""
        recommendations = []

        cpu = scan_data.get("cpu", {})
        if cpu.get("data", {}).get("average_usage_percent", 0) > 60:
            recommendations.append({
                "category": "CPU",
                "issue": "High CPU usage detected",
                "fix": "Disable startup programs, check for background processes",
                "impact": "High"
            })

        mem = scan_data.get("memory", {})
        if mem.get("data", {}).get("usage_percent", 0) > 70:
            recommendations.append({
                "category": "Memory",
                "issue": "High memory usage",
                "fix": "Close unused applications, add more RAM",
                "impact": "High"
            })

        disk = scan_data.get("disk", {})
        if disk.get("data", {}).get("partitions"):
            for part in disk["data"]["partitions"]:
                if part.get("usage_percent", 0) > 85:
                    recommendations.append({
                        "category": "Storage",
                        "issue": f"Drive {part.get('mountpoint', '')} nearly full",
                        "fix": "Run Disk Cleanup, delete temp files",
                        "impact": "Critical"
                    })

        return {
            "total_recommendations": len(recommendations),
            "critical": len([r for r in recommendations if r.get("impact") == "Critical"]),
            "recommendations": recommendations
        }


class AICodeAssistant:
    """AI assistant that can execute system commands and provide code solutions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)

    def generate_fix_script(self, issue_type: str) -> str:
        """Generate a PowerShell script to fix common issues."""
        scripts = {
            "cleanup": '''# Temp Files Cleanup Script
$ErrorActionPreference = 'SilentlyContinue'
$Cleaned = 0
$Size = 0

$Paths = @(
    $env:TEMP,
    "C:\\Windows\\Temp",
    "$env:LOCALAPPDATA\\Temp"
)

foreach ($Path in $Paths) {
    if (Test-Path $Path) {
        Get-ChildItem $Path -Recurse | ForEach-Object {
            $Size += $_.Length
            Remove-Item $_.FullName -Force -Recurse
            $Cleaned++
        }
    }
}

Write-Host "Cleaned $Cleaned files, freed $([math]::Round($Size/1MB)) MB"''',
            "network_reset": '''# Network Reset Script
Write-Host "Flushing DNS..."
ipconfig /flushdns | Out-Null

Write-Host "Releasing IP..."
ipconfig /release | Out-Null

Write-Host "Renewing IP..."
ipconfig /renew | Out-Null

Write-Host "Resetting Winsock..."
netsh winsock reset | Out-Null

Write-Host "Network reset complete. Restart recommended."''',
            "service_fix": '''# Fix Windows Services
$Services = @('wuauserv', 'BITS', 'Dnscache', 'Dhcp')

foreach ($svc in $Services) {
    Write-Host "Starting $svc..."
    Start-Service $svc -ErrorAction SilentlyContinue
}

Write-Host "Services checked."''',
            "disk_check": '''# Disk Health Check
Write-Host "Running disk check..."
chkdsk C: /f /r

Write-Host "Note: This requires restart. Schedule after saving work."''',
            "antivirus_enable": '''# Enable Windows Defender
Write-Host "Enabling Windows Defender..."

Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableBehaviorMonitoring $false

Write-Host "Real-time protection enabled."''',
            "firewall_enable": '''# Enable Windows Firewall
Write-Host "Enabling Firewall..."

Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

Write-Host "Firewall enabled for all profiles."''',
            "update_windows": '''# Force Windows Update
Write-Host "Checking for updates..."

$UpdateSession = New-Object -ComObject Microsoft.Update.Session
$UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
$SearchResult = $UpdateSearcher.Search("IsInstalled=0")

if ($SearchResult.Updates.Count -gt 0) {
    Write-Host "Installing $($SearchResult.Updates.Count) updates..."
    $Downloader = $UpdateSession.CreateUpdateDownloader()
    $Downloader.Updates = $SearchResult.Updates
    $Downloader.Download()

    $Installer = $UpdateSession.CreateUpdateInstaller()
    $Installer.Updates = $SearchResult.Updates
    $Installer.Install()

    Write-Host "Updates installed. Restart required."
} else {
    Write-Host "No updates available."
}''',
            "driver_update": '''# Check for driver updates
Write-Host "Opening Device Manager..."
devmgmt.msc

Write-Host("Manually check for driver updates:")
Write-Host("1. Right-click device > Update driver")
Write-Host("2. Search automatically for drivers")'''
        }

        return scripts.get(issue_type, "# Unknown issue type")

    def explain_issue(self, issue_title: str, issue_description: str) -> str:
        """Use AI to explain an issue in plain language."""
        if not self.client:
            return self._basic_explanation(issue_title)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"Explain this PC issue in simple terms:\n\nIssue: {issue_title}\nDetails: {issue_description}\n\nGive a 2-sentence explanation that a non-technical user can understand."
                }],
                max_tokens=150
            )
            return response.choices[0].message.content
        except:
            return self._basic_explanation(issue_title)

    def _basic_explanation(self, issue_title: str) -> str:
        explanations = {
            "cpu": "Your processor is working harder than normal, which can slow down your PC.",
            "memory": "Your computer is using most of its available RAM, which can cause lag.",
            "disk": "Your hard drive is running out of space, which affects performance.",
            "network": "There's a problem with your internet connection that needs attention.",
            "security": "Your PC may be vulnerable to threats and needs protection.",
            "service": "A Windows service that should be running is stopped.",
        }
        for key, desc in explanations.items():
            if key in issue_title.lower():
                return desc
        return "This issue may affect your PC's performance and should be addressed."


class MultiAIProvider:
    """Support for multiple AI providers (OpenAI, Claude, DeepSeek)"""

    def __init__(self, api_key: Optional[str] = None, provider: str = "auto"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("CLAUDE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        self.provider = provider.lower()
        self.client = None

        # Auto-detect provider based on key format
        if self.provider == "auto":
            if self.api_key and self.api_key.startswith("sk-"):
                self.provider = "openai"
            elif self.api_key and len(self.api_key) > 30:
                self.provider = "claude"
            elif self.api_key and self.api_key.startswith("ds-"):
                self.provider = "deepseek"
            else:
                self.provider = "openai"

        if self.provider == "openai" and self.api_key and OPENAI_AVAILABLE:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)

        elif self.provider == "claude" and self.api_key:
            self.claude_key = self.api_key

        elif self.provider == "deepseek" and self.api_key:
            self.deepseek_key = self.api_key

    def analyze_with_ai(self, prompt: str) -> str:
        """Use configured AI provider to analyze."""

        # OpenAI
        if self.provider == "openai" and self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"OpenAI Error: {e}"

        # Claude
        elif self.provider == "claude" and self.claude_key:
            try:
                import requests
                headers = {
                    "x-api-key": self.claude_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                }
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                if resp.status_code == 200:
                    return resp.json().get("content", [{}])[0].get("text", "")
                return f"Claude API Error: {resp.status_code}"
            except Exception as e:
                return f"Claude Error: {e}"

        # DeepSeek
        elif self.provider == "deepseek" and self.deepseek_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {self.deepseek_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                }
                resp = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                )
                if resp.status_code == 200:
                    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                return f"DeepSeek API Error: {resp.status_code}"
            except Exception as e:
                return f"DeepSeek Error: {e}"

        return "AI not configured. Set OPENAI_API_KEY, CLAUDE_API_KEY, or DEEPSEEK_API_KEY."


class UniversalAI:
    """Universal AI that automatically selects the best available provider."""

    def __init__(self):
        self.providers = {}

        # Check all available providers
        openai_key = os.environ.get("OPENAI_API_KEY")
        claude_key = os.environ.get("CLAUDE_API_KEY")
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY")

        if openai_key and OPENAI_AVAILABLE:
            self.providers["openai"] = MultiAIProvider(openai_key, "openai")

        if claude_key:
            self.providers["claude"] = MultiAIProvider(claude_key, "claude")

        if deepseek_key:
            self.providers["deepseek"] = MultiAIProvider(deepseek_key, "deepseek")

    @property
    def available(self) -> bool:
        return len(self.providers) > 0

    @property
    def provider_name(self) -> str:
        if not self.providers:
            return "None"
        # Prefer order: OpenAI > Claude > DeepSeek
        if "openai" in self.providers:
            return "OpenAI"
        elif "claude" in self.providers:
            return "Claude"
        elif "deepseek" in self.providers:
            return "DeepSeek"
        return "None"

    def ask(self, prompt: str) -> str:
        """Ask AI - automatically uses best available provider."""
        if "openai" in self.providers:
            return self.providers["openai"].analyze_with_ai(prompt)
        elif "claude" in self.providers:
            return self.providers["claude"].analyze_with_ai(prompt)
        elif "deepseek" in self.providers:
            return self.providers["deepseek"].analyze_with_ai(prompt)
        return "No AI provider available. Configure an API key."

    def diagnose_issue(self, issue_title: str, issue_description: str) -> str:
        """Get AI diagnosis for a specific issue."""
        prompt = f"""You are a PC diagnostics expert. Explain this issue simply:

Issue: {issue_title}
Details: {issue_description}

Give:
1. What causes this problem (simple terms)
2. How to fix it (step by step)
3. Why it matters

Keep it brief and friendly."""
        return self.ask(prompt)

    def optimize_system(self, scan_results: dict) -> str:
        """Get AI-powered optimization suggestions."""
        prompt = f"""As a PC expert, analyze this system data and give optimization advice:

{str(scan_results)[:2000]}

Provide:
1. Top 3 issues to fix
2. Best performance tips
3. Any hardware upgrade suggestions

Be practical and specific."""
        return self.ask(prompt)


def test_ai_connection():
    """Test AI connection with current configuration."""
    print("\n" + "="*50)
    print("   AI CONNECTION TEST")
    print("="*50)

    openai_key = os.environ.get("OPENAI_API_KEY")
    claude_key = os.environ.get("CLAUDE_API_KEY")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")

    if openai_key:
        print(f"[*] OpenAI API Key: {openai_key[:10]}...")
        ai = MultiAIProvider(openai_key, "openai")
        result = ai.analyze_with_ai("Say 'AI is working!' in 3 words")
        print(f"  Response: {result[:100]}")
    else:
        print("[ ] OpenAI API Key: Not set")

    if claude_key:
        print(f"[*] Claude API Key: {claude_key[:10]}...")
    else:
        print("[ ] Claude API Key: Not set")

    if telegram_token:
        print(f"[*] Telegram Bot: Configured")
    else:
        print("[ ] Telegram Bot: Not set")

    print("="*50 + "\n")


if __name__ == "__main__":
    test_ai_connection()
