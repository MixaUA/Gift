import json
import os
import logging
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Конфігурація логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфігурація моделі та файлів
CONTENT_FILE = 'content.json'
BIRTHDAY_FILE = 'birthday.json'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
KYIV_TZ = ZoneInfo("Europe/Kyiv")

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

# Глобальний стан черги моделей (пам'ять між викликами)
MODELS_STATE = [
    "gemini-2.0-flash", 
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]

def get_today():
    return datetime.now(KYIV_TZ).strftime("%Y-%m-%d")

def load_data():
    """Безпечне завантаження JSON із захистом від порожніх файлів."""
    if not os.path.exists(CONTENT_FILE):
        return {}
    
    try:
        with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"Файл {CONTENT_FILE} порожній. Повертаємо порожній словник.")
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Помилка читання JSON з {CONTENT_FILE}. Файл пошкоджено. Скидаємо дані.")
        return {}

def save_data(data):
    with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_gemini(prompt, force_json=False):
    """Виклик Gemini з динамічним зсувом черги моделей при 429/503."""
    global MODELS_STATE
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if force_json:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
    
    # Працюємо по стабільній копії поточної черги
    current_queue = list(MODELS_STATE)
    
    for model_id in current_queue:
        url = f"{GEMINI_API_BASE.format(model=model_id)}?key={GEMINI_API_KEY}"
        logger.info(f"Спроба з моделлю: {model_id}")
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
            
            elif response.status_code in (429, 503):
                logger.warning(f"Модель {model_id} зайнята ({response.status_code}). Переміщуємо в кінець черги.")
                if model_id in MODELS_STATE:
                    MODELS_STATE.remove(model_id)
                    MODELS_STATE.append(model_id)
                continue # Миттєво переходим до наступної моделі без сну!
                
            else:
                logger.error(f"Помилка {model_id}: {response.status_code} - {response.text}")
                if model_id in MODELS_STATE:
                    MODELS_STATE.remove(model_id)
                    MODELS_STATE.append(model_id)
                continue
                
        except Exception as e:
            logger.error(f"Помилка запиту до {model_id}: {e}")
            continue
            
    return None

def generate_confession():
    logger.info("Генерація нового зізнання для Вікторії...")
    prompt = """
    Напиши дуже коротке (строго 2-3 речення) романтичне, але зріле зізнання в коханні дружині Вікторії від чоловіка Михайла. Вони разом уже понад 20 років, тому текст має бути глибоким, спокійним і затишним, без підліткового пафосу чи надриву.
    
    СУВОРІ ПРАВИЛА:
    1. Грамматика: Тільки від першої особи чоловічого роду (я) до жінки (ти, твоя, кохана, рідна). ЖОДНИХ слешів на кшталт "думав/думала".
    2. Стиль: Проста, жива, сучасна українська мова. Текст має звучати так, ніби чоловік обійняв дружину вранці на кухні і тихо сказав це на вушко.
    3. Табу на слова: "єство", "буття", "доля", "океан", "всесвіт", "промовляти", "мій дорогий". 
    4. Зміст: Натякни на цінність прожитих разом років, на те, що її посмішка чи погляд досі є найнадійнішим і найріднішим домом у світі.
    5. Ніяких вигаданих чи прямих цитат класиків у лапках — просто цілісний, щирий текст від серця.
    """
    text = call_gemini(prompt)
    return text.strip() if text else None

def generate_enigma():
    logger.info("Генерація нового шифру...")
    prompt = """Загадай подію, пов'язану з коханням або романтикою (книга, вірш, пісня, картина).
    1. Подія повинна мати одну, чітко визначену дату створення або публікації (рік, 4 цифри).
    2. Сформулюй запитання про цю подію українською мовою (наприклад: "В якому році...").
    3. Відповідь має бути ТІЛЬКИ JSON формату: {"question": "...", "answer": "YYYY"}.
    4. Ніяких діапазонів. Тільки JSON."""
    text = call_gemini(prompt, force_json=True)
    
    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"ШІ повернув невалідний JSON: {text}")
    return None

def polybius_encode(text):
    grid = [
        ['А','Б','В','Г','Ґ','Д'],
        ['Е','Є','Ж','З','И','І'],
        ['Ї','Й','К','Л','М','Н'],
        ['О','П','Р','С','Т','У'],
        ['Ф','Х','Ц','Ч','Ш','Щ'],
        ['Ь','Ю','Я','.',',',' ']
    ]
    
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
    return " ".join(encoded)

def main():
    init_files()
    data = load_data()
    today = get_today()
    logger.info(f"Початок перевірки для дати: {today}")
    
    changed = False

    # Етап 1: Конфесія
    if data.get("confession_date") != today:
        logger.info("Confession застаріла. Оновлення...")
        text = generate_confession()
        if text:
            data["confession_text"] = text
            data["confession_date"] = today
            changed = True
            logger.info("Confession успішно оновлено.")
        else:
            logger.error("Помилка генерації тексту конфесії. Пропускаємо до наступного запуску.")
    else:
        logger.info("Confession актуальна.")

    # Етап 2: Питання/Відповідь (Enigma)
    if data.get("enigma_date") != today:
        logger.info("Enigma застаріла. Оновлення...")
        enigma = generate_enigma()
        if enigma:
            data["enigma_data"] = {"question": enigma["question"], "answer": enigma["answer"]}
            data["enigma_date"] = today
            changed = True
            logger.info("Enigma успішно оновлено.")
        else:
            logger.error("Помилка генерації шифру. Пропускаємо до наступного запуску.")
    else:
        logger.info("Enigma актуальна.")

    # Етап 3: Кодування
    if data.get("coding_date") != today and "enigma_data" in data:
        logger.info("Coding застаріла. Оновлення...")
        encoded = polybius_encode(data["enigma_data"]["question"])
        data["encoded_question"] = encoded
        data["coding_date"] = today
        changed = True
        logger.info("Кодування успішно оновлено.")
    else:
        logger.info("Кодування актуальне або відсутні дані для нього.")

    # Фінальне збереження прогресу
    if changed:
        save_data(data)
        logger.info("Файл контенту успішно збережено (зафіксовано оновлені етапи).")
    else:
        logger.info("Змін немає, файл не перезаписувався.")

    logger.info("Роботу завершено.")

if __name__ == "__main__":
    main()
