import requests
import json
import os
import google.generativeai as genai
from flask import Flask, request, Response

# --- Инициализация Flask ---
app = Flask(__name__)

# --- КЛЮЧИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
VIBER_AUTH_TOKEN = os.environ.get("VIBER_AUTH_TOKEN")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Конфигурация Google AI ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Ошибка: GEMINI_API_KEY не найден в переменных окружения.")

# --- Функция для получения новостей (без изменений) ---
def get_latest_news(category='general'):
    print(f"Запрошена категория: {category}")
    try:
        url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=ru&max=3&apikey={NEWS_API_KEY}" # Уменьшим до 3 для более глубокого анализа
        response = requests.get(url)
        data = response.json()
        if "articles" in data and data["articles"]:
            news_list = []
            for article in data['articles']:
                news_item = f"Заголовок: {article['title']}. Источник: {article['source']['name']}."
                news_list.append(news_item)
            return "\n".join(news_list)
        else:
            print(f"Для категории '{category}' не найдено статей. Ответ API: {data}")
            return None
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")
        return None

# --- ОБНОВЛЕННАЯ ФУНКЦИЯ АНАЛИЗА НОВОСТЕЙ С ПОМОЩЬЮ ИИ ---
def summarize_news_with_ai(news_text):
    if not news_text:
        return "Не удалось получить новости для анализа."
    print("Отправляем текст в Gemini для глубокого анализа...")
    try:
        # Для более глубокого анализа можно использовать модель 'gemini-1.5-pro', но она медленнее. 'flash' - хороший баланс.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # НОВЫЙ, УЛУЧШЕННЫЙ ПРОМПТ
        prompt = (
            "Ты — ведущий аналитик международного информационного агентства, специализирующийся на геополитике и технологиях, как сотрудник The Economist или Stratfor. "
            "Твоя задача — не просто пересказать новости, а дать глубокий, но сжатый анализ ситуации.\n\n"
            "Проанализируй каждую новость из списка ниже. Для каждой новости предоставь ответ в следующем структурированном виде:\n\n"
            "**Заголовок:** (Здесь заголовок новости)\n"
            "**Краткая суть:** (В 1-2 предложениях, что произошло)\n"
            "**Анализ и прогноз:** (Здесь твое видение. Каковы возможные последствия? Какой скрытый контекст? Кто ключевые игроки и каковы их мотивы? Что может произойти дальше? Свяжи это событие с более широкими трендами.)\n\n"
            "Сохраняй объективный и взвешенный тон. Отделяй каждую новость тремя дефисами (---).\n\n"
            "Вот новости для анализа:\n"
            f"{news_text}"
        )
        
        response = model.generate_content(prompt)
        print("Аналитика от Gemini получена.")
        return response.text
    except Exception as e:
        print(f"Ошибка при обращении к Gemini API: {e}")
        return "Извините, ИИ-аналитик временно перегружен и не может предоставить глубокий анализ."

# --- Остальные функции (create_main_keyboard, send_message, incoming, и т.д.) остаются без изменений ---

def create_main_keyboard():
    return { "Type": "keyboard", "Buttons": [
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/news", "Text": "🌐 Главные" },
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/politics", "Text": "🏛️ Политика" },
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/tech", "Text": "💻 Технологии" },
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/sport", "Text": "⚽ Спорт" },
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/science", "Text": "🔬 Наука" },
            { "Columns": 3, "Rows": 1, "ActionType": "reply", "ActionBody": "/health", "Text": "❤️ Здоровье" } ]}

def send_message(receiver_id, text, keyboard=None):
    print(f"--> Попытка отправить сообщение пользователю {receiver_id}...")
    headers = {"X-Viber-Auth-Token": VIBER_AUTH_TOKEN}
    payload = { "receiver": receiver_id, "min_api_version": 7, "sender": {"name": "Trumper"}, "type": "text", "text": text }
    if keyboard: payload['keyboard'] = keyboard
    try:
        response = requests.post("https://chatapi.viber.com/pa/send_message", json=payload, headers=headers)
        print(f"<-- Ответ от Viber API для пользователя {receiver_id}: Статус-код = {response.status_code}")
    except Exception as e:
        print(f"Критическая ошибка при отправке сообщения в Viber для пользователя {receiver_id}: {e}")

@app.route('/', methods=['POST'])
def incoming():
    viber_request = request.get_json()
    print(f"\n--- Получен новый запрос от Viber ---\n{viber_request}")

    if viber_request.get('event') == 'message':
        sender_id = viber_request['sender']['id']
        print(f"Это сообщение от пользователя с ID: {sender_id}")
        message_text = viber_request['message']['text'].lower()
        category_to_fetch = None
        
        if message_text in ["/news", "/general"]: category_to_fetch = "general"
        elif message_text == "/politics": category_to_fetch = "politics"
        elif message_text == "/tech": category_to_fetch = "technology"
        elif message_text == "/sport": category_to_fetch = "sports"
        elif message_text == "/science": category_to_fetch = "science"
        elif message_text == "/health": category_to_fetch = "health"
        
        if category_to_fetch:
            send_message(sender_id, f"Ищу новости и подключаю ИИ-аналитика...")
            news = get_latest_news(category=category_to_fetch)
            if news:
                summary = summarize_news_with_ai(news)
                send_message(sender_id, summary)
            else:
                send_message(sender_id, f"Не удалось найти актуальные новости по категории '{category_to_fetch}'.")
        else:
            help_text = "Привет! Я новостной бот-аналитик Trumper. Выберите категорию для получения сводки и анализа:"
            main_keyboard = create_main_keyboard()
            send_message(sender_id, help_text, main_keyboard)
    
    return Response(status=200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
