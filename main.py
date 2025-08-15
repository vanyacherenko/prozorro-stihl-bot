import requests
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Завантаження змінних
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Список чатів
CHAT_IDS = ["1971727077", "7981671066"]

CHECK_INTERVAL = 60  # сек
STATUS_INTERVAL = 86400  # сек
KEYWORDS = [ "stihl", "бензопила", ... ]  # твої ключові слова
seen_ids = set()
last_status = time.monotonic()
last_offset = None

# Відправка в Telegram
def send_message(msg):
    for cid in CHAT_IDS:
        data = {"chat_id": cid, "text": msg}
        resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=data)
        if resp.status_code != 200:
            print("Не надіслано:", resp.text)

# Prozorro API
def fetch_prozorro():
    global last_offset
    url = "https://public.api.openprocurement.org/api/2.5/tenders"
    params = {"limit": 100, "descending": "1"}
    if last_offset:
        params["offset"] = last_offset
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        print("Errored Prozorro:", resp.status_code); return []
    js = resp.json()
    last_offset = js.get("next_page", {}).get("offset", last_offset)
    return js.get("data", [])

# Pars Zakupivli.pro
def fetch_zakupivli():
    url = "https://zakupivli.pro/en"  # або конкретний розділ/фільтр
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        print("Ошибка Zakupivli:", resp.status_code); return []
    soup = BeautifulSoup(resp.text, "html.parser")
    tenders = []
    for block in soup.select("div.your-selector"):
        title = block.select_one("h3").text.strip()
        tid = block.select_one("a")["href"]
        desc = block.select_one("p.desc").text.strip()
        tenders.append({"id": tid, "title": title, "description": desc})
    return tenders

# Перевірка релевантності
def is_rel(t):
    txt = (t.get("title", "") + t.get("description", "")).lower()
    return any(k in txt for k in KEYWORDS)

# Формат повідомлення
def fmt(t, src):
    return f"[{src}] {t.get('title', 'No title')}\n{t.get('description', '')[:200]}...\nID: {t.get('id')}"

# Головна функція
def main():
    global last_status
    while True:
        now = time.monotonic()
        if now - last_status > STATUS_INTERVAL:
            send_message("Бот працює — " + datetime.now().isoformat())
            last_status = now

        for src, fetch in [("Prozorro", fetch_prozorro), ("Zakupivli", fetch_zakupivli)]:
            tenders = fetch()
            print(f"{src}: отримано {len(tenders)} тендерів")
            for t in tenders:
                tid = t.get("id")
                if tid and tid not in seen_ids and is_rel(t):
                    send_message(fmt(t, src))
                seen_ids.add(tid)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()




















