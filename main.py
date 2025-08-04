import requests
import time
from datetime import datetime, timezone, timedelta

# ======== Налаштування =========
KEYWORDS = [
    "stihl", "штиль", "штиль україна", "бензопила", "мотопила", "chainsaw",
    "ms 170", "ms 180", "ms 211", "ms 230", "ms 250", "ms 260",
    "ms 261", "ms 271", "ms 290", "ms 311", "ms 361", "ms 362",
    "ms 391", "ms 400", "ms 441", "ms 461", "ms 462", "ms 500", "ms 500i",
    "ms 661", "ms 880", "msa 120", "msa 140", "msa 160", "msa 200", "msa 220",
    "мотокоса", "коса", "trimmer", "тример", "fs 38", "fs 55", "fs 70", "fs 94",
    "fs 120", "fs 131", "fs 250", "fs 260", "fs 360", "fs 410", "fs 460", "fs 490",
    "кущоріз", "кущорізи", "hs 45", "hs 56", "hs 82", "hs 87", "висоторіз", "ht 75",
    "ht 101", "ht 131", "повітродувка", "повітродув", "пилосос", "br 200", "br 350",
    "br 430", "br 600", "br 700", "br 800", "садовий подрібнювач", "подрібнювач гілок",
    "gh 370", "gh 460", "мийка високого тиску", "мийка", "reh 120", "reh 160",
    "мотобур", "bt 121", "bt 131", "генератор stihl", "ланцюг", "шина", "масло stihl",
    "запчастини stihl", "стартер", "фільтр повітряний", "свічка запалювання"
]

CHECK_INTERVAL = 5  # кожні 5 секунд
STATUS_INTERVAL = 3600  # кожну годину (3600 секунд)
TELEGRAM_TOKEN = "7596129263:AAGPhGmxG7d1ECKAd7SMu8HlBQBboGhCO4M"
CHAT_ID = "1971727077"

seen_ids = set()
last_status_time = datetime.now()

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
        print("❌ Виняток під час надсилання:", e)

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
            print("❌ Помилка запиту:", response.status_code)
            return []
        return response.json().get("data", [])
    except Exception as e:
        print("❌ Виняток при запиті:", e)
        return []

def is_relevant(tender):
    title = tender.get("title", "").lower()
    description = tender.get("description", "").lower()
    combined_text = title + " " + description
    return any(keyword in combined_text for keyword in KEYWORDS)

def format_message(tender):
    return (
        f"🔔 *Виявлена закупівля STІHL-типу!*\n"
        f"📌 Назва: {tender.get('title', 'Без назви')}\n"
        f"🏢 Замовник: {tender.get('procuringEntity', {}).get('name', 'Невідомо')}\n"
        f"🌍 Область: {tender.get('procuringEntity', {}).get('address', {}).get('region', 'Невідомо')}\n"
        f"🔗 https://prozorro.gov.ua/tender/{tender.get('id')}"
    )

def main():
    global last_status_time
    while True:
        try:
            now = datetime.now()
            if (now - last_status_time).total_seconds() > STATUS_INTERVAL:
                send_message("✅ Програма працює — " + now.strftime("%Y-%m-%d %H:%M:%S"))
                last_status_time = now

            print("🔎 Перевірка закупівель...")
            tenders = search_prozorro()
            for tender in tenders:
                tid = tender["id"]
                if tid in seen_ids:
                    continue
                if is_relevant(tender):
                    msg = format_message(tender)
                    send_message(msg)
                seen_ids.add(tid)
        except Exception as e:
            print("❌ Помилка в циклі:", e)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()














