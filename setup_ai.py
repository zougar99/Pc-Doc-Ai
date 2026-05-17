"""
API Key Setup for PC Doctor AI
Easy configuration for AI and Telegram
"""

import os
import sys

CONFIG_FILE = "config.ini"


def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value
    return config


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


def setup_openai():
    print("\n" + "="*50)
    print("   SETUP OPENAI API KEY")
    print("="*50)
    print("\nTo get an OpenAI API key:")
    print("1. Go to https://platform.openai.com")
    print("2. Sign up or login")
    print("3. Go to API > Keys")
    print("4. Create a new secret key")
    print("5. Copy the key (starts with sk-)")
    print("-"*50)

    api_key = input("\nEnter your OpenAI API key: ").strip()

    if api_key.startswith("sk-"):
        print("\n[+] Valid key format!")
        config = load_config()
        config["OPENAI_API_KEY"] = api_key
        save_config(config)
        os.environ["OPENAI_API_KEY"] = api_key
        print("[+] API key saved to config.ini")
        print("[+] Also set as environment variable")

        print("\n[*] Testing connection...")
        try:
            from ai_engine import MultiAIProvider
            ai = MultiAIProvider(api_key, "openai")
            result = ai.analyze_with_ai("Say OK if you work")
            if "OK" in result or "ok" in result.lower():
                print("[+] AI is working!")
            else:
                print("[*] Key saved but response unusual")
        except Exception as e:
            print(f"[-] Test error: {e}")

    else:
        print("\n[!] Invalid key format. Should start with 'sk-'")


def setup_claude():
    print("\n" + "="*50)
    print("   SETUP CLAUDE API KEY")
    print("="*50)
    print("\nTo get a Claude API key:")
    print("1. Go to https://console.anthropic.com")
    print("2. Sign up or login")
    print("3. Go to API Keys")
    print("4. Create a new key")
    print("5. Copy the key")
    print("-"*50)

    api_key = input("\nEnter your Claude API key: ").strip()

    if len(api_key) > 20:
        print("\n[+] Key format looks valid")
        config = load_config()
        config["CLAUDE_API_KEY"] = api_key
        save_config(config)
        os.environ["CLAUDE_API_KEY"] = api_key
        print("[+] API key saved!")
    else:
        print("\n[!] Key seems too short")


def setup_telegram():
    print("\n" + "="*50)
    print("   SETUP TELEGRAM BOT")
    print("="*50)
    print("\nFollow these steps:")
    print("1. Open Telegram, search @BotFather")
    print("2. Send /newbot to create a new bot")
    print("3. Follow instructions and get the token")
    print("4. Open your bot and send /start")
    print("5. Get your chat_id from @userinfobot")
    print("-"*50)

    token = input("\nEnter Telegram Bot Token: ").strip()
    chat_id = input("Enter Telegram Chat ID: ").strip()

    if token and chat_id:
        config = load_config()
        config["TELEGRAM_BOT_TOKEN"] = token
        config["TELEGRAM_CHAT_ID"] = chat_id
        save_config(config)
        os.environ["TELEGRAM_BOT_TOKEN"] = token
        os.environ["TELEGRAM_CHAT_ID"] = chat_id

        print("\n[+] Telegram configured!")

        print("\n[*] Testing...")
        try:
            from telegram_bot import TelegramNotifier
            notifier = TelegramNotifier(token, chat_id)
            result = notifier.send_alert("test", "PC Diagnostic connected!")
            if result.get("success"):
                print("[+] Test message sent!")
            else:
                print(f"[-] Error: {result.get('error')}")
        except Exception as e:
            print(f"[-] Error: {e}")


def show_current_config():
    print("\n" + "="*50)
    print("   CURRENT CONFIGURATION")
    print("="*50)

    config = load_config()

    openai = config.get("OPENAI_API_KEY", "")
    claude = config.get("CLAUDE_API_KEY", "")
    telegram = config.get("TELEGRAM_BOT_TOKEN", "")

    if openai:
        print(f"[+] OpenAI: {openai[:15]}...")
    else:
        print("[ ] OpenAI: Not set")

    if claude:
        print(f"[+] Claude: {claude[:15]}...")
    else:
        print("[ ] Claude: Not set")

    if telegram:
        print(f"[+] Telegram: Configured")
    else:
        print("[ ] Telegram: Not set")

    print("="*50)


def main():
    while True:
        print("\n" + "="*50)
        print("   API & CONFIGURATION SETUP")
        print("="*50)
        print("""
  [1] Setup OpenAI API Key
  [2] Setup Claude API Key
  [3] Setup Telegram Bot
  [4] Show Current Config
  [5] Test All Connections
  [6] Exit
""")
        choice = input("Select: ").strip()

        if choice == "1":
            setup_openai()
        elif choice == "2":
            setup_claude()
        elif choice == "3":
            setup_telegram()
        elif choice == "4":
            show_current_config()
        elif choice == "5":
            from ai_engine import test_ai_connection
            test_ai_connection()
        elif choice == "6":
            print("\nDone!")
            break


if __name__ == "__main__":
    main()