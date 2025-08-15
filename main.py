import requests
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Завантаження токена та чатів з .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = ["197172707"]  # ID користувачів, яким надсилати повідомлення

# Ключові слова для пошуку у назві/описі
KEYWORDS = [
    "stihl", "штиль", "мотопила", "бензопила", "газонокосарка",
    "мотокоса", "триммер", "кущоріз", "повітродувка", "пилосос",
    "мотокультиватор", "садова техніка", "запасні частини stihl",
    "ланцюг", "шина", "фільтр stihl", "олива stihl"
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

# Список вже відправлених тендерів
sent_tenders = set()

def send_telegram_message(text):
    """Відправка повідомлення у Telegram"""
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        requests.post(url, data=payload)

def fetch_new_tenders():
    """Отримання нових тендерів з Prozorro"""
    url = "https://public.api.openprocurement.org/api/2.5/tenders?feed=changes&mode=real_time"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json().get("data", [])
        return data
    return []

def process_tender(tender_id):
    """Обробка тендеру та перевірка на ключові слова або код ДК"""
    tender_url = f"https://public.api.openprocurement.org/api/2.5/tenders/{tender_id}"
    response = requests.get(tender_url)
    if response.status_code != 200:
        return
    
    tender = response.json().get("data", {})
    title = tender.get("title", "").lower()
    description = tender.get("description", "").lower()
    cpv_code = tender.get("items", [{}])[0].get("classification", {}).get("id", "")

    # Перевірка на ключові слова або код ДК
    if any(keyword in title or keyword in description for keyword in KEYWORDS) or cpv_code in DK_CODES:
        # Формуємо повідомлення
        tender_link = f"https://prozorro.gov.ua/tender/{tender_id}"
        message = f"🆕 <b>Новий тендер</b>\n\n" \
                  f"📌 <b>{tender.get('title')}</b>\n" \
                  f"📅 Дата: {tender.get('datePublished')}\n" \
                  f"📑 Код ДК: {cpv_code}\n" \
                  f"🔗 {tender_link}"
        
        # Надсилаємо тільки якщо не відправляли раніше
        if tender_id not in sent_tenders:
            send_telegram_message(message)
            sent_tenders.add(tender_id)

def main():
    """Основний цикл програми"""
    while True:
        try:
            tenders = fetch_new_tenders()
            for tender in tenders:
                tender_id = tender.get("id")
                if tender_id and tender_id not in sent_tenders:
                    process_tender(tender_id)
            time.sleep(60)  # Перевірка кожну хвилину
        except Exception as e:
            print(f"❌ Помилка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()























