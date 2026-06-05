import json
import os
import logging
import random
import requests
from datetime import datetime
import zoneinfo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONTENT_FILE = 'content.json'
BIRTHDAY_FILE = 'birthday.json'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# =============================================================================
# GEMINI CLIENT (gemini-2.5-flash тепер перша)
# =============================================================================

MODELS_STATE = [
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]

# =============================================================================
# PROMPT ENGINE — константи для варіативності
# =============================================================================

CONFESSION_TOPICS = [
    "голос", "погляд", "усмішка", "ніжність", "довіра",
    "захищеність", "натхнення", "вдячність", "захоплення", "турбота",
    "сила", "спокій", "очікування", "сум за нею", "щастя від її присутності",
    "гордість за неї", "її тиша", "їїスміх", "її дотик", "її світло",
    "її мовчання", "її погляд збоку", "її присутність", "її тепло",
    "те як вона слухає", "те як вона дивиться", "те як вона усміхається",
    "те як вона мовчить", "те як вона торкається", "радість від неї",
]

MOOD_REGISTERS = [
    "ніжний, затишний і трохи акварельний",
    "глибокий, злегка задумливий і спокійний",
    "грайливий, легкий і теплий",
    "щирий, безпосередній, як раптова думка",
]

CONFESSION_STYLES = [
    "внутрішній монолог — ніби чоловік думає про неї вголос, дивлячись у вікно",
    "тихе звернення — затишна розмова наодинці, фокус на одному миттєвому відчутті",
    "кінематографічний кадр — опис моменту, де деталі (світло, тиша, її присутність) передають любов",
    "проста подяка — безпафосне визнання того, як її існування змінює все навколо",
    "раптове відкриття — коли посеред дня гостро відчуваєш, як сильно любиш",
    "метафора дня — одне красиве порівняння відчуття кохання з чимось простим і справжнім",
    "визнання слабкості — щирі слова про те, як її спокій захищає від усього зовнішнього шуму",
    "тиха радість — світлий і дуже чистий текст про те, як добре просто бути в одному просторі",
    "дивування — коли дивишся на неї і досі не можеш повірити своєму щастю",
    "обіцянка без клятв — тихе внутрішнє рішення берегти це тепло щодня",
]

# =============================================================================
# STATE LOGIC — ключі JSON
# =============================================================================

FRONTEND_KEYS = {
    "confession_text",
    "confession_date",
    "enigma_data",
    "enigma_date",
    "encoded_question",
    "coding_date",
}

AI_KEYS = {
    "confession_topics_recent",   # max 30
    "confession_styles_recent",   # max 10
    "enigma_authors_recent",      # max 30
    "day_counter",                # лічильник днів для визначення deep day
}

def init_files():
    if not os.path.exists(CONTENT_FILE):
        logger.info(f"Створення порожнього {CONTENT_FILE}")
        with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    if not os.path.exists(BIRTHDAY_FILE):
        logger.info(f"Створення порожнього {BIRTHDAY_FILE}")
        with open(BIRTHDAY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"text": "Вітаю з днем народження!"}, f)

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

def clean_data(data):
    """Видаляє застарілі ключі та обрізає АІ-списки для підтримання гігієни JSON."""
    allowed_keys = FRONTEND_KEYS | AI_KEYS
    stale = [k for k in list(data.keys()) if k not in allowed_keys]
    for k in stale:
        logger.info(f"Видаляємо застарілий ключ: '{k}'")
        del data[k]

    if "confession_topics_recent" in data:
        data["confession_topics_recent"] = data["confession_topics_recent"][:30]
    if "confession_styles_recent" in data:
        data["confession_styles_recent"] = data["confession_styles_recent"][:10]
    if "enigma_authors_recent" in data:
        data["enigma_authors_recent"] = data["enigma_authors_recent"][:30]

    return data

def save_data(data):
    with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def call_gemini(prompt, force_json=False, creative=False):
    global MODELS_STATE
    if creative:
        gen_config = {"temperature": 1.18, "topP": 0.98, "topK": 50}
    else:
        gen_config = {"temperature": 1.05, "topP": 0.92, "topK": 32}
    if force_json:
        gen_config["responseMimeType"] = "application/json"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }

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

def pick_topic(recent_topics):
    available = [t for t in CONFESSION_TOPICS if t not in recent_topics]
    if not available:
        logger.warning("Всі теми вичерпано — скидаємо список.")
        available = CONFESSION_TOPICS
    topic = random.choice(available)
    logger.info(f"Обрана тема: '{topic}'")
    return topic

def pick_style(recent_styles):
    available = [s for s in CONFESSION_STYLES if s not in recent_styles]
    if not available:
        logger.warning("Всі стилі вичерпано — скидаємо список.")
        available = CONFESSION_STYLES
    style = random.choice(available)
    logger.info(f"Обраний стиль: '{style}'")
    return style

def is_deep_day(day_counter):
    return day_counter > 0 and day_counter % 7 == 0

def _parse_confession_response(raw):
    if not raw:
        return None, None
    topic = None
    text = None
    for line in raw.strip().splitlines():
        if line.startswith("ТЕМА:"):
            topic = line.replace("ТЕМА:", "").strip()
        elif line.startswith("ТЕКСТ:"):
            text = line.replace("ТЕКСТ:", "").strip()
    if not text:
        logger.warning("Модель не дотрималась формату ТЕМА/ТЕКСТ — використовуємо повну відповідь.")
        text = raw.strip()
    return text, topic

def generate_confession_light(topic, style, recent_topics=None):
    """Легке, але надзвичайно художнє зізнання."""
    mood = random.choice(MOOD_REGISTERS)
    logger.info(f"Легкий день. Регістр настрою: '{mood}'")

    recent_block = ""
    if recent_topics:
        topics_str = "\n".join(f"- {t}" for t in recent_topics)
        recent_block = f"ВИКОРИСТАНІ РАНІШЕ ТЕМИ (не повторюй образи з них):\n{topics_str}"

    prompt = f"""Напиши коротке романтичне зізнання в коханні від чоловіка до дружини.

ТЕМА СЬОГОДНІ: {topic}
СТИЛЬ ПОДАЧІ: {style}
НАСТРІЙ: {mood}

ХУДОЖНІ ПРАВИЛА:
1. Мова — жива, природна, тепла українська. Без штучного пафосу, театральності чи поетичних штампів. Пиши так, ніби це тиха розмова наодинці.
2. Текст має бути чітко адресованим і створювати відчуття близькості. Якщо ти описуєш якусь деталь (руку, погляд, усмішку), обов'язково пов'язуй її з нею: використовуй займенники "твоєї", "твій", "твоїх", "твій", щоб було зрозуміло, що це стосується її (наприклад: "торкаючись твоєї долоні", "у твоєму погляді").
3. Уникай надмірного повторення займенників "я" та "мій" там, де дію можна зрозуміти з закінчення дієслова (замість "я відчуваю" пиши "відчуваю").
4. Текстура та деталі: дозволено згадувати універсальні речі (тиша, тепло рук, погляд, напівсонна посмішка, ранкове світло), але категорично ЗАБОРОНЕНО вигадувати неіснуючий побут (кава в ліжко, прогулянки під дощем тощо).
5. Граматика: від першої особи чоловічого роду до жінки.
6. ОБСЯГ: рівно 4-5 речень. Зберігай легкість і ритмічний баланс.

ЗВЕРТАННЯ: Дозволено використати ТІЛЬКИ ОДНЕ звернення на весь текст, і лише всередині речення (не на початку): "Кохана", "Рідна моя" або "Серце моє". Будь-які інші звернення (на кшталт "світло моє", "сонце") — суворе ТАБУ.
ТАБУ НА СЛОВА ТА ІМЕНА: без імені дружини, без дат чи тривалості стосунків. Жодних слів типу "всесвіт", "океан почуттів", "доля", "єство", "промовляти".

{recent_block}

ФОРМАТ ВІДПОВІДІ — рівно два рядки (без преамбул та маркдауну):
ТЕМА: {topic}
ТЕКСТ: <саме зізнання>
"""
    return _parse_confession_response(call_gemini(prompt, creative=False))

def generate_confession_deep(topic, style, recent_topics=None):
    """Глибокий день (кожен 7-й день). Створення глибокого емоційного зв'язку через один образ."""
    logger.info("Глибокий день. Генерація особливого поетичного зізнання...")

    recent_block = ""
    if recent_topics:
        topics_str = "\n".join(f"- {t}" for t in recent_topics)
        recent_block = f"ВИКОРИСТАНІ РАНІШЕ ТЕМИ (уникай подібних метафор):\n{topics_str}"

    prompt = f"""Напиши особливе, художньо глибоке зізнання в коханні від чоловіка до дружини.

ТЕМА СЬОГОДНІ: {topic}
СТИЛЬ ПОДАЧІ: {style}

ПРАВИЛА ОСОБЛИВОГО СТИЛЮ (DEEP):
1. Напиши текст, зосереджений навколо ОДНОГО сильного образа чи метафори. Розгортай його неспішно.
2. Тон має бути зрілим, спокійним і дуже інтимним. Текст має чітко зв'язувати автора і дружину — використовуй присвійні займенники ("твоєї", "твоїх", "твій"), щоб опис деталей звучав природно та адресно (наприклад: "у твоєму погляді", "тепло твоєї руки").
3. Використовуй паузи, нерівний ритм, іноді незавершені думки — це робить мову живою та щирою. Повністю уникай штампів про кохання.
4. Максимально очисти текст від слів-паразитів "я" та "мій", залишаючи фокус на ній та ваших спільних відчуттях.
5. ОБСЯГ: 3–5 речень. Краще менше речень, але нехай кожне слово буде точним.

ЗВЕРТАННЯ: Дозволено використати ТІЛЬКИ ОДНЕ звернення на весь текст, і лише всередині речення: "Кохана", "Рідна моя" або "Серце моє". Будь-які інші варіанти (на кшталт "світло моє") — під забороною.
ТАБУ: жодних імен, дат, років, побутових вигадок.

{recent_block}

ФОРМАТ ВІДПОВІДІ — рівно два рядки (без преамбул та маркдауну):
ТЕМА: {topic}
ТЕКСТ: <саме зізнання>
"""
    return _parse_confession_response(call_gemini(prompt, creative=True))

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

# =============================================================================
# MAIN
# =============================================================================

def main():
    init_files()
    data = load_data()
    data = clean_data(data)  # Безпечне очищення при кожному запуску
    today = get_today()
    logger.info(f"Початок перевірки для дати: {today}")
    changed = False

    # --- Етап 1: Confession ---
    if data.get("confession_date") != today:
        logger.info("Confession застаріла. Оновлення...")

        recent_topics = data.get("confession_topics_recent", [])
        recent_styles = data.get("confession_styles_recent", [])
        topic = pick_topic(recent_topics)
        style = pick_style(recent_styles)

        day_counter = data.get("day_counter", 0) + 1

        if is_deep_day(day_counter):
            logger.info("Сьогодні ГЛИБОКИЙ день (кожен 7-й).")
            text, _ = generate_confession_deep(topic=topic, style=style, recent_topics=recent_topics)
        else:
            text, _ = generate_confession_light(topic=topic, style=style, recent_topics=recent_topics)

        if text:
            data["confession_text"] = text
            data["confession_date"] = today
            data["day_counter"] = day_counter  # Оновлюємо лічильник тільки при успішній генерації
            
            recent_topics = ([topic] + recent_topics)[:30]
            data["confession_topics_recent"] = recent_topics
            
            recent_styles = ([style] + recent_styles)[:10]
            data["confession_styles_recent"] = recent_styles
            
            logger.info(f"Тему збережено: '{topic}'. Стиль: '{style}'. День: {day_counter}.")
            changed = True
            logger.info("Confession успішно оновлено.")
        else:
            logger.error("Помилка генерації тексту конфесії. Пропускаємо до наступного запуску.")
    else:
        logger.info("Confession актуальна.")

    # --- Етап 2: Enigma ---
    if data.get("enigma_date") != today:
        logger.info("Enigma застаріла. Оновлення...")
        recent_authors = data.get("enigma_authors_recent", [])
        enigma = generate_enigma(recent_authors=recent_authors)
        if enigma:
            data["enigma_data"] = {"question": enigma["question"], "answer": enigma["answer"]}
            data["enigma_date"] = today
            if enigma.get("author"):
                new_author = enigma["author"]
                recent_authors = ([new_author] + recent_authors)[:30]
                data["enigma_authors_recent"] = recent_authors
                logger.info(f"Автора збережено: '{new_author}'.")
            changed = True
            logger.info("Enigma успішно оновлено.")
        else:
            logger.error("Помилка генерації шифру. Пропускаємо до наступного запуску.")
    else:
        logger.info("Enigma актуальна.")

    # --- Етап 3: Кодування ---
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
        logger.info("Файл контенту успішно збережено.")
    else:
        logger.info("Змін немає, файл не перезаписувався.")

    logger.info("Роботу завершено.")

if __name__ == "__main__":
    main()
