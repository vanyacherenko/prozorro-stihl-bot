import requests
import time

BOT_TOKEN = "8047019586:AAEJiYwmR-jlP5WtPHz440nrP7Df-NY31mg"
CHAT_ID = "1971727077"

KEYWORDS = [
    "мотокоса", "бензопила", "ланцюгова пила", "газонокосарка", "тример", "повітродувка",
    "кущоріз", "висоторіз", "обприскувач", "акумуляторна техніка", "електропила",
    "двигун внутрішнього згоряння", "двотактний двигун", "садова техніка"
]
REGION_FILTER = "Чернігівська"
PROCUREMENT_METHODS = ["aboveThresholdUA", "belowThreshold"]  # Відкриті торги та спрощена

BASE_URL = "https://public.api.openprocurement.org/api/2.5/tenders"
SEEN_IDS = set()


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)


def check_new_tenders():
    try:
        response = requests.get(f"{BASE_URL}?limit=20")
        tenders = response.json()["data"]

        for item in tenders:
            tender_id = item["id"]
            if tender_id in SEEN_IDS:
                continue
            SEEN_IDS.add(tender_id)

            # Завантаження повної інформації про тендер
            tender_url = f"{BASE_URL}/{tender_id}"
            tender_data = requests.get(tender_url).json()["data"]

            # Фільтр за регіоном
            region = tender_data.get("procuringEntity", {}).get("address", {}).get("region", "")
            if REGION_FILTER.lower() not in region.lower():
                continue

            # Фільтр за типом закупівлі
            procurement_method_type = tender_data.get("procurementMethodType", "")
            if procurement_method_type not in PROCUREMENT_METHODS:
                continue

            title = tender_data.get("title", "").lower()
            description = tender_data.get("description", "").lower()
            items = tender_data.get("items", [])

            # Аналіз найменувань і тех. характеристик
            matches = []
            for item in items:
                name = item.get("description", "").lower()
                if any(kw in name for kw in KEYWORDS):
                    matches.append(item)

            if not matches:
                continue

            # Формування повідомлення
            tender_link = f"https://prozorro.gov.ua/tender/{tender_id}"
            customer = tender_data.get("procuringEntity", {}).get("name", "Невідомо")
            expected_value = tender_data.get("value", {}).get("amount", 0)
            currency = tender_data.get("value", {}).get("currency", "UAH")

            items_info = ""
            for match in matches:
                price = match.get("value", {}).get("amount", "Не вказано")
                name = match.get("description", "Без опису")
                items_info += f"\n- *{name}*, 💸 {price} {currency}"

            message = (
                f"🔔 *Виявлена релевантна закупівля STІHL-типу!*"
                f"🆔 ID: `{tender_id}`\n"
                f"📦 Товари: {items_info}\n"
                f"💰 Очікувана вартість: {expected_value} {currency}\n"
                f"🏢 Замовник: {customer}\n"
                f"🔗 [Переглянути на Prozorro]({tender_link})"
            )
            send_telegram_message(message)

    except Exception as e:
        print(f"Помилка: {e}")


if __name__ == "__main__":
    print("📡 Запуск моніторингу тендерів STІHL...")
    while True:
        check_new_tenders()
        time.sleep(1)  # кожні 1 секунд
