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
genai.configure(api_key=GEMINI_API_KEY)


# --- Функция для получения новостей (без изменений) ---
def get_latest_news(category='general'):
    print(f"Запрошена категория: {category}")
    try:
        url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=ru&max=5&apikey={NEWS_API_KEY}"
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


# --- Функция для создания сводки с помощью ИИ (без изменений) ---
def summarize_news_with_ai(news_text):
    if not news_text:
        return "Не удалось получить новости для анализа."
    print("Отправляем текст в Gemini для создания сводки...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            "Ты — профессиональный новостной редактор. "
            "Проанализируй следующий набор новостных заголовков. "
            "Напиши одну связную, краткую сводку (не более 3-4 предложений) на русском языке, излагая главные события. "
            "Не используй Markdown, просто верни чистый текст.\n\n"
            "Вот новости:\n"
            f"{news_text}"
        )
        response = model.generate_content(prompt)
        print("Сводка от Gemini получена.")
        return response.text
    except Exception as e:
        print(f"Ошибка при обращении к Gemini API: {e}")
        return "Извините, ИИ-аналитик временно недоступен."

# --- НОВАЯ ФУНКЦИЯ: Создаем клавиатуру с кнопками ---
def create_main_keyboard():
    """Создает и возвращает JSON-объект клавиатуры для Viber."""
    return {
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/news", "Text": "🌐 Главные"
            },
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/politics", "Text": "🏛️ Политика"
            },
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/tech", "Text": "💻 Технологии"
            },
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/sport", "Text": "⚽ Спорт"
            },
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/science", "Text": "🔬 Наука"
            },
            {
                "Columns": 3, "Rows": 1, "ActionType": "reply",
                "ActionBody": "/health", "Text": "❤️ Здоровье"
            }
        ]
    }

# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ОТПРАВКИ СООБЩЕНИЙ: теперь с поддержкой клавиатуры ---
def send_message(receiver_id, text, keyboard=None):
    """Отправляет сообщение пользователю Viber, опционально с клавиатурой."""
    print(f"Попытка отправить сообщение пользователю {receiver_id}...")
    headers = {"X-Viber-Auth-Token": VIBER_AUTH_TOKEN}
    payload = {
        "receiver": receiver_id, "min_api_version": 7, # <-- Увеличили версию API для поддержки клавиатур
        "sender": {"name": "Trumper"}, "type": "text", "text": text
    }
    # Если передана клавиатура, добавляем ее в тело запроса
    if keyboard:
        payload['keyboard'] = keyboard
    
    try:
        response = requests.post("https://chatapi.viber.com/pa/send_message", json=payload, headers=headers)
        print(f"Ответ от Viber API: Статус-код = {response.status_code}, Тело ответа = {response.text}")
    except Exception as e:
        print(f"Критическая ошибка при отправке сообщения в Viber: {e}")


# --- ГЛАВНАЯ ЛОГИКА БОТА: изменена отправка приветственного сообщения ---
@app.route('/', methods=['POST'])
def incoming():
    viber_request = request.get_json()

    if viber_request['event'] == 'message':
        message_text = viber_request['message']['text'].lower()
        sender_id = viber_request['sender']['id']
        
        category_to_fetch = None
        
        if message_text in ["/news", "/general"]: category_to_fetch = "general"
        elif message_text == "/politics": category_to_fetch = "politics"
        elif message_text == "/tech": category_to_fetch = "technology"
        elif message_text == "/sport": category_to_fetch = "sports"
        elif message_text == "/science": category_to_fetch = "science"
        elif message_text == "/health": category_to_fetch = "health"
        # entertainment убрали, чтобы кнопки красиво смотрелись
        
        if category_to_fetch:
            send_message(sender_id, f"Ищу новости и готовлю ИИ-аналитика...")
            news = get_latest_news(category=category_to_fetch)
            if news:
                summary = summarize_news_with_ai(news)
                send_message(sender_id, summary) # Отправляем сводку без клавиатуры
            else:
                send_message(sender_id, f"Не удалось найти актуальные новости по категории '{category_to_fetch}'.")
        else:
            # --- Теперь отправляем приветствие вместе с клавиатурой ---
            help_text = "Привет! Я новостной бот Trumper. Выберите категорию новостей:"
            main_keyboard = create_main_keyboard()
            send_message(sender_id, help_text, main_keyboard) # Передаем клавиатуру в функцию
    
    return Response(status=200)

# --- Запускаем наш сервер (без изменений) ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
