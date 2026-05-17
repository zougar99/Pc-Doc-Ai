"""
Telegram Bot for PC Doctor AI
Sends scan results and alerts to Telegram
"""

import os
import requests
import json
from datetime import datetime


class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else None

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str, parse_mode="Markdown") -> dict:
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}

        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=data, timeout=10)
            return {"success": response.status_code == 200, "response": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_scan_results(self, health_score: float, issues: list, system_info: dict) -> dict:
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}

        score_emoji = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"

        message = f"*PC Doctor AI Scan Results*\n"
        message += f"{'='*30}\n\n"
        message += f"*Health Score:* {score_emoji} {health_score}/100\n\n"
        message += f"*System Info:*\n"
        message += f"• OS: {system_info.get('os', 'N/A')}\n"
        message += f"• RAM: {system_info.get('ram', 'N/A')}\n"
        message += f"• CPU: {system_info.get('cpu', 'N/A')}\n\n"

        if issues:
            critical = [i for i in issues if i.get("severity") == "critical"]
            warnings = [i for i in issues if i.get("severity") == "warning"]

            if critical:
                message += f"*⚠️ Critical Issues ({len(critical)}):*\n"
                for i in critical[:3]:
                    message += f"• {i.get('title', 'Unknown')}\n"
                message += "\n"

            if warnings:
                message += f"*⚡ Warnings ({len(warnings)}):*\n"
                for i in warnings[:5]:
                    message += f"• {i.get('title', 'Unknown')}\n"

        message += f"\n*Scan Time:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return self.send_message(message)

    def send_alert(self, alert_type: str, message: str) -> dict:
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}

        emoji = {
            "critical": "🔴",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        text = f"*PC Alert - {alert_type}*\n{emoji.get(alert_type, '⚡')} {message}\n\nTime: {datetime.now().strftime('%H:%M:%S')}"
        return self.send_message(text)

    def send_html_report(self, html_content: str) -> dict:
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}

        try:
            url = f"{self.api_url}/sendDocument"
            files = {"document": ("report.html", html_content, "text/html")}
            data = {"chat_id": self.chat_id, "caption": "PC Diagnostic Report"}
            response = requests.post(url, files=files, data=data, timeout=30)
            return {"success": response.status_code == 200, "response": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


def setup_telegram():
    print("\n" + "="*50)
    print("   TELEGRAM BOT SETUP")
    print("="*50)
    print("\nTo receive scan results on Telegram:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Create a new bot: /newbot")
    print("3. Copy the bot token")
    print("4. Start a chat with your bot")
    print("5. Go to https://api.telegram.org/bot<TOKEN>/getUpdates")
    print("6. Copy your chat_id from the JSON response")
    print("\nThen set environment variables:")
    print('  set TELEGRAM_BOT_TOKEN=your_bot_token')
    print('  set TELEGRAM_CHAT_ID=your_chat_id')
    print("\nOr add to the application directly.")
    print("="*50 + "\n")


if __name__ == "__main__":
    setup_telegram()
    notifier = TelegramNotifier()
    if notifier.is_configured:
        print("Telegram configured!")
        print(notifier.send_alert("info", "Test message from PC Diagnostic"))
    else:
        print("Telegram not configured. Run setup above.")