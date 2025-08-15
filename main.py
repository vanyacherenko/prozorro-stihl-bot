import requests
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Завантаження змінних з .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Список ID користувачів, яким надсилаємо повідомлення
CHAT_IDS = [
    "1971727077",  # ← твоє
    "7981671066",  # ← додаєш нових сюди
]

CHECK_INTERVAL = 30        # Перевірка кожні 30 сек
STATUS_INTERVAL = 86400    # Раз на добу надсилати "Програма працює"
TARGET_REGION = "чернігівська область"

# Ключові слова для пошуку
KEYWORDS = [
    "stihl", "штиль", "штиль україна", "бензопила", "мотопила", "chainsaw",
    "ms 170", "ms 180", "ms 211", "ms 230", "ms 250", "ms 260", "ms 261",
    "ms 271", "ms 290", "ms 311", "ms 361", "ms 362", "ms 391", "ms 400",
    "ms 441", "ms 461", "ms 462", "ms 500", "ms 500i", "ms 661", "ms 880",
    "msa 120", "msa 140", "msa 160", "msa 200", "msa 220", "мотокоса", "коса",
    "trimmer", "тример", "fs 38", "fs 55", "fs 70", "fs 94", "fs 120", "fs 131",
    "fs 250", "fs 260", "fs 360", "fs 410", "fs 460", "fs 490", "кущоріз",
    "hs 45", "hs 56", "hs 82", "hs 87", "висоторіз", "ht 75", "ht 101",
    "ht 131", "повітродувка", "повітродув", "пилосос", "br 200", "br 350",
    "br 430", "br 600", "br 700", "br 800", "подрібнювач", "gh 370", "gh 460",
    "мийка", "reh 120", "reh 160", "мотобур", "bt 121", "bt 131",
    "генератор stihl", "ланцюг", "шина", "масло stihl", "запчастини",
    "стартер", "фільтр", "свічка"
]

seen_ids = set()
last_status_time = time.monotonic()
last_offset = None  # Зберігаємо останній offset для безперервної роботи

# Відправка повідомлення в Telegram
def send_message(text):
    for chat_id in CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"❌ Не надіслано {chat_id}:", response.text)
            else:
                print(f"✅ Надіслано {chat_id}: {text[:50]}")
        except Exception as e:
            print(f"❌ Помилка {chat_id}:", e)

# Пошук тендерів на Prozorro
def search_prozorro():
    global last_offset
    url = "https://public.api.openprocurement.org/api/2.5/tenders"

    params = {
        "limit": 100,  # щоб не забивати сервер
        "descending": "1"
    }
    if last_offset:
        params["offset"] = last_offset

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print("❌ Запит не вдався:", response.status_code)
            return []

        json_data = response.json()
        last_offset = json_data.get("next_page", {}).get("offset", last_offset)
        tenders = json_data.get("data", [])

        print(f"📥 Отримано {len(tenders)} тендерів.")
        return tenders

    except Exception as e:
        print("❌ Помилка при запиті:", e)
        return []

# Перевірка на відповідність ключовим словам та регіону
def is_relevant(tender):
    text = (tender.get("title", "") + " " + tender.get("description", "")).lower()
    # region = tender.get("procuringEntity", {}).get("address", {}).get("region", "").lower()
    # return any(keyword in text for keyword in KEYWORDS) and TARGET_REGION in region
    return any(keyword in text for keyword in KEYWORDS)

# Формування повідомлення
def format_message(tender):
    return (
        f"🔔 Виявлена закупівля STІHL-типу!\n"
        f"📌 Назва: {tender.get('title', 'Без назви')}\n"
        f"🏢 Замовник: {tender.get('procuringEntity', {}).get('name', 'Невідомо')}\n"
        f"🌍 Область: {tender.get('procuringEntity', {}).get('address', {}).get('region', 'Невідомо')}\n"
        f"🔗 https://prozorro.gov.ua/tender/{tender.get('tenderID', tender.get('id'))}"
    )

# Головний цикл програми
def main():
    global last_status_time
    while True:
        try:
            now = time.monotonic()

            # Раз на добу надсилати повідомлення, що програма працює
            if now - last_status_time > STATUS_INTERVAL:
                send_message("✅ Програма працює — " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                last_status_time = now

            print("🔍 Перевірка тендерів...")
            tenders = search_prozorro()

            for tender in tenders:
                tid = tender.get("id")
                if tid and tid not in seen_ids:
                    if is_relevant(tender):
                        send_message(format_message(tender))
                    seen_ids.add(tid)

        except Exception as e:
            print("❌ Помилка в циклі:", e)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()





















