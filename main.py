import requests
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# 🔹 Завантаження змінних середовища з файлу .env
load_dotenv()

# ========= Налаштування =========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 5  # кожні 5 секунд перевіряти Prozorro
STATUS_INTERVAL = 3600  # кожну годину надсилати "програма працює"

# Ключові слова, що шукаються у назві або описі тендеру
KEYWORDS = [
    "stihl", "штиль", "штиль україна", "бензопила", "мотопила", "chainsaw",
    "ms 170", "ms 180", "ms 211", "ms 230", "ms 250", "ms 260", "ms 261",
    "ms 271", "ms 290", "ms 311", "ms 361", "ms 362", "ms 391", "ms 400",
    "ms 441", "ms 461", "ms 462", "ms 500", "ms 500i", "ms 661", "ms 880",
    "msa 120", "msa 140", "msa 160", "msa 200", "msa 220", "мотокоса", "коса",
    "trimmer", "тример", "fs 38", "fs 55", "fs 70", "fs 94", "fs 120", "fs 131",
    "fs 250", "fs 260", "fs 360", "fs 410", "fs 460", "fs 490", "кущоріз", "hs 45",
    "hs 56", "hs 82", "hs 87", "висоторіз", "ht 75", "ht 101", "ht 131", "повітродувка",
    "повітродув", "пилосос", "br 200", "br 350", "br 430", "br 600", "br 700", "br 800",
    "подрібнювач", "gh 370", "gh 460", "мийка", "reh 120", "reh 160", "мотобур", "bt 121",
    "bt 131", "генератор stihl", "ланцюг", "шина", "масло stihl", "запчастини", "стартер",
    "фільтр", "свічка"
]

seen_ids = set()  # запам'ятовуємо оброблені тендери, щоб уникати дублювання
last_status_time = datetime.now()

# 🔹 Відправка повідомлення в Telegram
def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print("❌ Помилка надсилання:", response.text)
        else:
            print("✅ Повідомлення надіслано:", text[:50])
    except Exception as e:
        print("❌ Виняток при надсиланні:", e)

# 🔹 Запит до Prozorro API
def search_prozorro():
    url = "https://public.api.openprocurement.org/api/2.5/tenders"
    params = {
        "offset": datetime.now(timezone.utc).isoformat(),
        "limit": 1000,
        "descending": "1",
        "mode": "test.exclusion"
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print("❌ Запит неуспішний:", response.status_code)
            return []
        return response.json().get("data", [])
    except Exception as e:
        print("❌ Помилка запиту:", e)
        return []

# 🔹 Визначення, чи є тендер релевантним
def is_relevant(tender):
    title = tender.get("title", "").lower()
    description = tender.get("description", "").lower()
    combined = title + " " + description
    return any(keyword in combined for keyword in KEYWORDS)

# 🔹 Формування тексту повідомлення
def format_message(tender):
    return (
        f"🔔 Виявлена закупівля STІHL-типу!\n"
        f"📌 Назва: {tender.get('title', 'Без назви')}\n"
        f"🏢 Замовник: {tender.get('procuringEntity', {}).get('name', 'Невідомо')}\n"
        f"🌍 Область: {tender.get('procuringEntity', {}).get('address', {}).get('region', 'Невідомо')}\n"
        f"🔗 https://prozorro.gov.ua/tender/{tender.get('id')}"
    )

# 🔹 Основний цикл роботи програми
def main():
    global last_status_time
    while True:
        try:
            now = datetime.now()
            # Щогодини надсилати повідомлення, що програма працює
            if (now - last_status_time).total_seconds() > STATUS_INTERVAL:
                send_message("✅ Програма працює — " + now.strftime("%Y-%m-%d %H:%M:%S"))
                last_status_time = now

            print("🔎 Перевірка нових тендерів...")
            tenders = search_prozorro()
            for tender in tenders:
                tid = tender["id"]
                if tid in seen_ids:
                    continue  # пропускаємо оброблені
                if is_relevant(tender):
                    msg = format_message(tender)
                    send_message(msg)
                seen_ids.add(tid)  # запам'ятовуємо
        except Exception as e:
            print("❌ Помилка в циклі:", e)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()















