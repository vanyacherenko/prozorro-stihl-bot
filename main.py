import requests
import time
import datetime
import telegram

# ======== Налаштування =========
KEYWORDS = ["stihl", "штиль", "ms 361", "ms 362", "ms 461", "ms 462", "ms 661", "ms 500"]
REGION = "Чернігівська область"
CHECK_INTERVAL = 1  # перевіряти кожні 1 хвилин
TELEGRAM_TOKEN = "8047019586:AAEJiYwmR-jlP5WtPHz440nrP7Df-NY31mg"
CHAT_ID = "1971727077"

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def search_prozorro():
    url = "https://public.api.openprocurement.org/api/2.5/tenders"
    params = {
        "offset": datetime.datetime.utcnow().isoformat(),
        "limit": 100,
        "descending": "1",
        "mode": "test.exclusion"  # щоб виключити тестові
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print("Помилка запиту до Prozorro")
        return []
    return response.json().get("data", [])

def is_relevant(tender):
    title = tender.get("title", "").lower()
    description = tender.get("description", "").lower()
    region = tender.get("procuringEntity", {}).get("address", {}).get("region", "")
    combined_text = title + description
    return (
        any(keyword in combined_text for keyword in KEYWORDS) and
        REGION.lower() in region.lower()
    )

def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode=telegram.constants.ParseMode.MARKDOWN)
    except Exception as e:
        print("Помилка надсилання повідомлення:", e)

def format_message(tender):
    return (
        f"🔔 *Виявлена релевантна закупівля STІHL-типу!*\n"
        f"📌 Назва: {tender.get('title', 'Без назви')}\n"
        f"🏢 Замовник: {tender.get('procuringEntity', {}).get('name', 'Невідомо')}\n"
        f"🌍 Область: {tender.get('procuringEntity', {}).get('address', {}).get('region', 'Невідомо')}\n"
        f"🔗 https://prozorro.gov.ua/tender/{tender.get('id')}"
    )

seen_ids = set()

while True:
    try:
        tenders = search_prozorro()
        for tender in tenders:
            if tender["id"] in seen_ids:
                continue
            if is_relevant(tender):
                msg = format_message(tender)
                send_message(msg)
            seen_ids.add(tender["id"])
    except Exception as ex:
        print("Помилка в головному циклі:", ex)
    time.sleep(CHECK_INTERVAL)
