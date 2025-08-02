import requests
import time
from datetime import datetime, timezone
import telegram

# ======== Налаштування =========
KEYWORDS = [
    "stihl", "штиль", "штиль україна",
    # Мотопили (бензопили)
    "бензопила", "мотопила", "chainsaw",
    "ms 170", "ms 180", "ms 211", "ms 230", "ms 250", "ms 260",
    "ms 261", "ms 271", "ms 290", "ms 311", "ms 361", "ms 362",
    "ms 391", "ms 400", "ms 441", "ms 461", "ms 462", "ms 500",
    "ms 500i", "ms 661", "ms 880",
    # Акумуляторні пили
    "msa 120", "msa 140", "msa 160", "msa 200", "msa 220",
    # Коси, мотокоси, тримери
    "мотокоса", "коса", "trimmer", "тример",
    "fs 38", "fs 55", "fs 70", "fs 94", "fs 120", "fs 131",
    "fs 250", "fs 260", "fs 360", "fs 410", "fs 460", "fs 490",
    # Кущорізи, ножиці
    "кущоріз", "кущорізи", "hs 45", "hs 56", "hs 82", "hs 87",
    # Висоторізи
    "висоторіз", "ht 75", "ht 101", "ht 131",
    # Повітродувки, пилососи
    "повітродувка", "повітродув", "пилосос",
    "br 200", "br 350", "br 430", "br 600", "br 700", "br 800",
    # Подрібнювачі
    "садовий подрібнювач", "подрібнювач гілок", "gh 370", "gh 460",
    # Мийки високого тиску
    "мийка високого тиску", "мийка", "reh 120", "reh 160",
    # Мотобури
    "мотобур", "bt 121", "bt 131",
    # Генератори
    "генератор stihl",
    # Комплектуючі
    "ланцюг", "шина", "масло stihl", "запчастини stihl", "стартер", "фільтр повітряний", "свічка запалювання"]
# REGION = "Чернігівська область"
CHECK_INTERVAL = 5  # перевіряти кожні 5 c
TELEGRAM_TOKEN = "8047019586:AAEhziintMV5wDI2JOSPmPf76uuAhGGFbBA"
CHAT_ID = "1971727077"

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def search_prozorro():
    url = "https://public.api.openprocurement.org/api/2.5/tenders"
    params = {
        "offset":  "2025-03-01T00:00:00Z" #datetime.now(timezone.utc).isoformat(),
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
    combined_text = title + " " + description
    if not any(keyword in combined_text for keyword in KEYWORDS):
        return False
    # Якщо хочеш перевірку області, розкоментуй цей блок:
    # region = tender.get("procuringEntity", {}).get("address", {}).get("region", "")
    # if REGION.lower() not in region.lower():
    #     return False
    return True
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

