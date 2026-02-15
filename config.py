import os

# === STEAM API (4 ключа) ===
STEAM_API_KEYS = [
    "B7619F1D7DA6C8FF5895D2FFF8EA25D9",                   # ключ 2
    "C90BAB647AD944E55DC1422F043B851A",                    # ключ 3
    "3B4B2E38E01A7753AACB5A98F9647A71"                  # ключ 4
]

# === TELEGRAM ===
YOUR_BOT_TOKEN = "7801629582:AAFeLmb_GpHEUOPwm4wD_ewtNyQm6xCDDuE"
YOUR_CHAT_ID = 671116574

# === ФАЙЛЫ ===
WORDS_FILE = "3char.txt"
BANNED_FILE = "banned.txt"
ACCOUNTS_FILE = "accounts.txt"

def load_words():
    try:
        with open(WORDS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"❌ Файл {WORDS_FILE} не найден!")
        return []

def load_banned():
    try:
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_banned(word):
    with open(BANNED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n{word}")