import json
import os
import logging
import time
import requests
from datetime import datetime
import zoneinfo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONTENT_FILE = 'content.json'
BIRTHDAY_FILE = 'birthday.json'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

def init_files():
    if not os.path.exists(CONTENT_FILE):
        logger.info(f"Створення порожнього {CONTENT_FILE}")
        with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not os.path.exists(BIRTHDAY_FILE):
        logger.info(f"Створення порожнього {BIRTHDAY_FILE}")
        with open(BIRTHDAY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"text": "Вітаю з днем народження!"}, f)

MODELS_STATE = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]

def get_today():
    try:
        kyiv_tz = zoneinfo.ZoneInfo("Europe/Kyiv")
        return datetime.now(kyiv_tz).strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Помилка визначення часової зони Europe/Kyiv: {e}. Використовуємо системний час.")
        return datetime.now().strftime("%Y-%m-%d")

def load_data():
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
    global MODELS_STATE
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if force_json:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
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
                continue
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

def generate_confession(previous_confession=None, previous_topic=None):
    logger.info("Генерація нового зізнання...")

    prompt = """
    Напиши коротке (строго 4-5 речень) романтичне, ніжне зізнання в коханні дружині від чоловіка.
    Текст має бути глибоким, спокійним і затишним — без пафосу, надриву чи штучної піднесеності.

    СУВОРІ ПРАВИЛА:
    1. ОБ'ЄМ: Рівно 4-5 речень. Не менше, не більше.
    2. БЕЗ ІМЕНІ: Ніколи не звертайся по імені (не "Вікторіє", не "Віка").
    3. ЗВЕРТАННЯ — тільки одне з цих: "Кохана", "Рідна моя", "Сонечко моє", "Серце моє", "Люба моя", "Світло моє", "Найрідніша".
    4. БЕЗ ЧАСУ: Жодних років, дат, тривалості стосунків ("роки поруч", "десятиліття" — табу).
    5. ГРАМАТИКА: Від першої особи чоловічого роду до жінки. Ніяких слешів "коханий/кохана".
    6. СТИЛЬ: Жива, проста, сучасна українська. Як ніжний шепіт на вухо вранці — без гучних слів.
    7. ТАБУ НА СЛОВА: "єство", "буття", "доля", "океан почуттів", "всесвіт", "промовляти", "безмежний", "невимовний".
    8. БЕЗ ЦИТАТ: Ніяких вигаданих цитат класиків у лапках.
    9. ТІЛЬКИ ПОЧУТТЯ — БЕЗ ПОБУТУ: Текст про внутрішні відчуття чоловіка, а не опис спільних сцен чи звичок.
       ЗАБОРОНЕНО вигадувати конкретні деталі їхнього життя (каву, прогулянки, вечері, читання книг тощо) —
       бо вони можуть не відповідати реальності. Тільки те, що є правдою для будь-якої любові:
       відчуття її присутності, тепло від її існування поруч, спокій який вона дає, радість від її погляду чи усмішки.

    ТЕМИ ДЛЯ НАТХНЕННЯ — абстрактні відчуття (щодня обирай різну):
    її сміх, тепло її рук, її погляд, її голос,
    її внутрішнє світло, відчуття захищеності поруч з нею,
    спокій який вона дає, радість від її існування,
    її ніжність, сила яку він черпає з її любові.
    """

    if previous_topic:
        prompt += f"""
    9. ТАБУ НА ТЕМУ: Вчорашня тема була "{previous_topic}". Сьогодні ОБОВ'ЯЗКОВО обери іншу тему зі списку вище.
    """
    elif previous_confession:
        prompt += f"""
    9. ТАБУ НА ПОВТОРЕННЯ: Вчора було написано:
    ---
    "{previous_confession}"
    ---
    Сьогодні — абсолютно інша тема, інші метафори, інша структура речень.
    """

    prompt += """
    ФОРМАТ ВІДПОВІДІ — суворо два рядки, без зайвого тексту:
    ТЕМА: <одне-два слова — тема цього зізнання>
    ТЕКСТ: <саме зізнання 4-5 речень>
    """

    raw = call_gemini(prompt)
    if not raw:
        return None, None

    topic = None
    text = None
    for line in raw.strip().splitlines():
        if line.startswith("ТЕМА:"):
            topic = line.replace("ТЕМА:", "").strip()
        elif line.startswith("ТЕКСТ:"):
            text = line.replace("ТЕКСТ:", "").strip()

    # Якщо модель проігнорувала формат — повертаємо весь текст як є
    if not text:
        logger.warning("Модель не дотрималась формату ТЕМА/ТЕКСТ — використовуємо повну відповідь.")
        text = raw.strip()

    return text, topic

def generate_enigma(recent_authors=None):
    logger.info("Генерація нового шифру...")

    prompt = """Загадай відомий твір, пов'язаний з коханням або романтикою.

    ПРАВИЛА ВИБОРУ ТВОРУ:
    1. Жанр — обирай різноманітно: вірш, роман, опера, балет, картина, симфонія, пісня, поема, кіно.
    2. Автор має бути відомим, твір — реальним з точно відомим роком.
    3. Рік має бути єдиним і чітким (не діапазон).
    4. Питання формулюй українською: "В якому році...", "Коли вперше...", "У якому році написав...".
    """

    if recent_authors:
        authors_str = ", ".join(f'"{a}"' for a in recent_authors)
        prompt += f"""
    5. ТАБУ НА АВТОРІВ: Нещодавно вже були: {authors_str}.
       Обери автора якого НЕМАЄ в цьому списку. Інша країна, інший жанр.
    """

    prompt += """
    Відповідь — ТІЛЬКИ JSON без жодного додаткового тексту:
    {"question": "...", "answer": "YYYY", "author": "Ім'я Прізвище"}
    """

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
        old_topic = data.get("confession_topic")
        old_confession = data.get("confession_text")
        if old_topic:
            logger.info(f"Знайдено вчорашню тему: '{old_topic}'. Передаємо для уникнення повторів.")
        elif old_confession:
            logger.info("Теми немає — передаємо вчорашній текст для уникнення повторів.")
        text, topic = generate_confession(previous_confession=old_confession, previous_topic=old_topic)
        if text:
            data["confession_text"] = text
            data["confession_date"] = today
            if topic:
                data["confession_topic"] = topic
                logger.info(f"Тему збережено: '{topic}'")
            changed = True
            logger.info("Confession успішно оновлено.")
        else:
            logger.error("Помилка генерації тексту конфесії. Пропускаємо до наступного запуску.")
    else:
        logger.info("Confession актуальна.")

    # Етап 2: Питання/Відповідь (Enigma)
    if data.get("enigma_date") != today:
        logger.info("Enigma застаріла. Оновлення...")
        recent_authors = data.get("enigma_authors_recent", [])
        if recent_authors:
            logger.info(f"Останні автори: {recent_authors}. Передаємо для уникнення повторів.")
        enigma = generate_enigma(recent_authors=recent_authors)
        if enigma:
            data["enigma_data"] = {"question": enigma["question"], "answer": enigma["answer"]}
            data["enigma_date"] = today
            if enigma.get("author"):
                new_author = enigma["author"]
                recent_authors = ([new_author] + recent_authors)[:7]
                data["enigma_authors_recent"] = recent_authors
                logger.info(f"Автора збережено: '{new_author}'. Список останніх: {recent_authors}")
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

    if changed:
        save_data(data)
        logger.info("Файл контенту успішно збережено (зафіксовано оновлені етапи).")
    else:
        logger.info("Змін немає, файл не перезаписувався.")

    logger.info("Роботу завершено.")

if __name__ == "__main__":
    main()
