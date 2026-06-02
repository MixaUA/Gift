import json
import os
import re
import logging
import time
import requests

# Конфігурація логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфігурація моделі та файлів
CONTENT_FILE = 'content.json'
BIRTHDAY_FILE = 'birthday.json'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

def init_files():
    """Створення порожніх шаблонів, якщо файли відсутні."""
    if not os.path.exists(CONTENT_FILE):
        logger.info(f"Створення порожнього {CONTENT_FILE}")
        with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    
    if not os.path.exists(BIRTHDAY_FILE):
        logger.info(f"Створення порожнього {BIRTHDAY_FILE}")
        with open(BIRTHDAY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"text": "Вітаю з днем народження!"}, f)

# Каскад моделей
GEMINI_MODELS = [
    "gemini-2.0-flash", # Оновлена актуальна основна
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def load_data():
    if not os.path.exists(CONTENT_FILE):
        return {}
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_gemini(prompt):
    """Виклик Gemini з каскадом моделей та обробкою лімітів."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for model_id in GEMINI_MODELS:
        url = f"{GEMINI_API_BASE.format(model=model_id)}?key={GEMINI_API_KEY}"
        logger.info(f"Спроба з моделлю: {model_id}")
        
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return text
                elif response.status_code in (429, 503):
                    wait = (attempt + 1) * 30
                    logger.warning(f"Модель {model_id} зайнята ({response.status_code}), чекаю {wait}с.")
                    time.sleep(wait)
                else:
                    logger.error(f"Помилка {model_id}: {response.status_code} - {response.text}")
                    break # Переходимо до наступної моделі
            except Exception as e:
                logger.error(f"Помилка запиту до {model_id}: {e}")
                break
    return None

def generate_confession():
    logger.info("Генерація нового зізнання...")
    prompt = """
    Напиши коротке (3-4 речення), дуже інтимне, літературне зізнання в коханні.
    - Використай у тексті одну влучну, глибоку цитату про кохання від відомих класиків літератури або поетів.
    - Цитата повинна бути органічно вплетена в інтимний текст.
    - Без зайвого пафосу, максимально близько, ніби шепіт на вушко.
    """
    text = call_gemini(prompt)
    return text.strip() if text else None

def generate_enigma():
    logger.info("Генерація нового шифру...")
    prompt = """Загадай подію, пов'язану з коханням або романтикою (книга, вірш, пісня, картина).
    1. Подія повинна мати одну, чітко визначену дату створення або публікації (рік, 4 цифри).
    2. Сформулюй запитання про цю подію (наприклад: "В якому році...").
    3. Відповідь має бути ТІЛЬКИ JSON формату: {"question": "...", "answer": "YYYY"}.
    4. Ніяких діапазонів. Тільки JSON."""
    text = call_gemini(prompt)
    
    if text:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    return None

def polybius_encode(text):
    grid = [['А','Б','В','Г','Ґ','Д'],['Е','Є','Ж','З','И','І'],['Ї','Й','К','Л','М','Н'],['О','П','Р','С','Т','У'],['Ф','Х','Ц','Ч','Ш','Щ'],['Ь','Ю','Я','.',',',' ']]
    
    encoded = []
    for char in text.upper():
        found = False
        for i, row in enumerate(grid):
            for j, val in enumerate(row):
                if char == val:
                    encoded.append(f"{i+1}{j+1}")
                    found = True
                    break
            if found: break
        if not found: encoded.append("??")
    return " ".join(encoded)

def main():
    init_files()
    data = load_data()
    today = get_today()
    logger.info(f"Початок перевірки для дати: {today}")

    # Етап 1: Конфесія
    if data.get("confession_date") != today:
        logger.info("Confession застаріла. Оновлення...")
        text = generate_confession()
        if text:
            data["confession_text"] = text
            data["confession_date"] = today
            save_data(data)
            logger.info("Confession успішно оновлено.")
        else:
            logger.error("Помилка генерації тексту конфесії.")
            return
    else:
        logger.info("Confession актуальна.")

    # Етап 2: Питання/Відповідь (Enigma)
    if data.get("enigma_date") != today:
        logger.info("Enigma застаріла. Оновлення...")
        enigma = generate_enigma()
        if enigma:
            data["enigma_data"] = {"question": enigma["question"], "answer": enigma["answer"]}
            data["enigma_date"] = today
            save_data(data)
            logger.info("Enigma успішно оновлено.")
        else:
            logger.error("Помилка генерації шифру.")
            return
    else:
        logger.info("Enigma актуальна.")

    # Етап 3: Кодування
    if data.get("coding_date") != today:
        logger.info("Coding застаріла. Оновлення...")
        encoded = polybius_encode(data["enigma_data"]["question"])
        data["encoded_question"] = encoded
        data["coding_date"] = today
        save_data(data)
        logger.info("Кодування успішно оновлено.")
    else:
        logger.info("Кодування актуальне.")

    logger.info("Всі етапи завершені успішно.")

if __name__ == "__main__":
    main()
