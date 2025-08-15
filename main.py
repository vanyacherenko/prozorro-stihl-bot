import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Завантаження токена та чатів з .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = ["197172707"]

# Перевірка токена на старті
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN не знайдено у .env!")
    exit(1)
else:
    print(f"✅ .env завантажено, токен: {TELEGRAM_TOKEN[:5]}...")

# Повний список ключових слів
KEYWORDS = [
    "stihl", "штиль", "штиль україна", "бензопила", "мотопила", "chainsaw",
    "ms 170", "ms 180", "ms 211", "ms 230", "ms 250", "ms 260", "ms 261",
    "ms 271", "ms 290", "ms 311", "ms 361", "ms 362", "ms 391", "ms 400",
    "ms 441", "ms 461", "ms 462", "ms 500", "ms 500i", "ms 661", "ms 880",
    "msa 120", "msa 140", "msa 160", "msa 200", "msa 220", "мотокоса", "коса",
    "trimmer", "тример", "fs 38", "fs 55", "fs 70", "fs 94", "fs 120", "fs 131",
    "fs 250", "fs 260", "fs 360", "fs 410", "fs 460", "fs 490", "кущоріз", "hs 45",
    "hs 56", "hs 82", "hs 87", "висоторіз", "ht 75", "ht 101", "ht 131",
    "повітродувка", "повітродув", "пилосос", "br 200", "br 350", "br 430",
    "br 600", "br 700", "br 800", "подрібнювач", "gh 370", "gh 460", "мийка",
    "reh 120", "reh 160", "мотобур", "bt 121", "bt 131", "генератор stihl",
    "ланцюг", "шина", "масло stihl", "запчастини", "стартер", "фільтр", "свічка"
]

# Розширений список кодів ДК
DK_CODES = [
    "16100000-6", "16160000-4", "16162000-8", "16162100-9", "16162200-0",
    "16300000-8", "16310000-1", "16311000-8", "16311100-9", "16320000-4",
    "16340000-0", "16800000-3", "16810000-6", "16820000-9", "16830000-2",
    "16840000-5", "42650000-7", "42652000-1", "42660000-0", "44510000-8",
    "44511000-5", "44512000-2", "44512600-6", "44514000-6", "09211000-1",
    "09211100-2", "09211200-3", "42990000-2", "42993200-5", "42994000-9",
    "31400000-0", "31420000-6", "31421000-3", "39713430-2", "39713431-9",
    "39713432-6"
]

sent_tenders = set()  # Тендери, що вже були надіслані

def send_telegram_message(text):
    """Відправка повідомлення у Telegram з обробкою лімітів"""
    for chat_id in CHAT_IDS:
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
                response = requests.post(url, data=payload)
                
                if response.status_code == 429:
                    retry_after = response.json().get("parameters", {}).get("retry_after", 1)
                    print(f"⏳ Ліміт Telegram, чекаю {retry_after} сек...")
                    time.sleep(retry_after)
                    continue
                print(f"✅ Повідомлення надіслано у Telegram ({chat_id})")
                break
            except Exception as e:
                print(f"❌ Помилка Telegram: {e}")
                time.sleep(5)
                continue

def fetch_new_tenders():
    """Отримання нових тендерів в реальному часі"""
    url = "https://public.api.openprocurement.org/api/2.5/tenders?feed=changes&mode=real_time"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"❌ Помилка завантаження тендерів: {e}")
    return []

def is_keyword_in_text(text):
    if not text:
        return False
    return any(keyword.lower() in text.lower() for keyword in KEYWORDS)

def process_tender(tender_id):
    """Обробка тендера"""
    url = f"https://public.api.openprocurement.org/api/2.5/tenders/{tender_id}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return
        tender = response.json().get("data", {})
        title = tender.get("title", "").lower()
        description = tender.get("description", "").lower()
        cpv_codes = [item.get("classification", {}).get("id", "") for item in tender.get("items", [])]

        if is_keyword_in_text(title) or is_keyword_in_text(description) or any(cpv in DK_CODES for cpv in cpv_codes):
            tender_link = f"https://prozorro.gov.ua/tender/{tender_id}"
            message = f"🆕 <b>Новий тендер</b>\n\n" \
                      f"📌 <b>{tender.get('title')}</b>\n" \
                      f"📅 Дата: {tender.get('datePublished')}\n" \
                      f"📑 Коди ДК: {', '.join(cpv_codes)}\n" \
                      f"🔗 {tender_link}"
            if tender_id not in sent_tenders:
                send_telegram_message(message)
                sent_tenders.add(tender_id)

def main():
    print("🚀 Старт моніторингу нових тендерів STIHL...")
    while True:
        try:
            tenders = fetch_new_tenders()
            print(f"🔍 Перевірено {len(tenders)} нових тендерів ({datetime.now()})")
            for tender in tenders:
                tender_id = tender.get("id")
                if tender_id and tender_id not in sent_tenders:
                    process_tender(tender_id)
            time.sleep(15)  # перевірка кожні 15 секунд
        except Exception as e:
            print(f"❌ Помилка основного циклу: {e}")
            time.sleep(15)

if __name__ == "__main__":
    main()

























