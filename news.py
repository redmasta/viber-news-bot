import requests
import json
import google.generativeai as genai
from flask import Flask, request, Response

# --- Инициализация Flask ---
app = Flask(__name__)

# --- ВАШИ КЛЮЧИ И НАСТРОЙКИ ---
VIBER_AUTH_TOKEN = os.environ.get("VIBER_AUTH_TOKEN")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- Конфигурация Google AI ---
genai.configure(api_key=GEMINI_API_KEY)

# --- Функция для получения новостей (без изменений) ---
def get_latest_news(category='general'):
    """Получает последние 5 новостей по заданной категории."""
    print(f"Запрошена категория: {category}")
    try:
        url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=ru&max=5&apikey={NEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if "articles" in data and data["articles"]:
            news_list = []
            for article in data['articles']:
                # Собираем только заголовок и источник для анализа
                news_item = f"Заголовок: {article['title']}. Источник: {article['source']['name']}."
                news_list.append(news_item)
            return "\n".join(news_list) # Возвращаем сплошной текст для ИИ
        else:
            print(f"Для категории '{category}' не найдено статей. Ответ API: {data}")
            return None # Возвращаем None, если новостей нет
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")
        return None

# --- НОВАЯ ФУНКЦИЯ: Создание сводки с помощью ИИ ---
def summarize_news_with_ai(news_text):
    """Отправляет текст новостей в Gemini и получает краткую сводку."""
    if not news_text:
        return "Не удалось получить новости для анализа."
    
    print("Отправляем текст в Gemini для создания сводки...")
    try:
        # Выбираем модель (gemini-1.5-flash - быстрая и эффективная)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Создаем промпт (задание) для ИИ
        prompt = (
            "Ты — профессиональный новостной редактор. "
            "Проанализируй следующий набор новостных заголовков. "
            "Напиши одну связную, краткую сводку (не более 3-4 предложений) на русском языке, излагая главные события. "
            "Не используй Markdown, просто верни чистый текст.\n\n"
            "Вот новости:\n"
            f"{news_text}"
        )
        
        # Генерируем ответ
        response = model.generate_content(prompt)
        
        print("Сводка от Gemini получена.")
        return response.text

    except Exception as e:
        print(f"Ошибка при обращении к Gemini API: {e}")
        return "Извините, ИИ-аналитик временно недоступен."

# --- Функция для отправки сообщений в Viber (без изменений) ---
def send_message(receiver_id, text):
    headers = {"X-Viber-Auth-Token": VIBER_AUTH_TOKEN}
    payload = {
        "receiver": "QkA3Fd6/7rP9prh+PJLy1Q==",
        "min_api_version": 1,
        "sender": {"name": "Мой Новостной Бот"},
        "type": "text",
        "text": text
    }
    requests.post("https://chatapi.viber.com/pa/send_message", json=payload, headers=headers)

# --- ГЛАВНАЯ ЛОГИКА БОТА: теперь с вызовом ИИ ---
@app.route('/', methods=['POST'])
def incoming():
    viber_request = request.get_json()

    if viber_request['event'] == 'message':
        message_text = viber_request['message']['text'].lower()
        sender_id = viber_request['sender']['id']
        
        category_to_fetch = None
        
        if message_text in ["/news", "/general"]: category_to_fetch = "general"
        elif message_text == "/sport": category_to_fetch = "sports"
        elif message_text == "/tech": category_to_fetch = "technology"
        elif message_text == "/science": category_to_fetch = "science"
        elif message_text == "/health": category_to_fetch = "health"
        elif message_text == "/entertainment": category_to_fetch = "entertainment"

        if category_to_fetch:
            send_message(sender_id, f"Ищу новости и готовлю ИИ-аналитика...")
            
            # Шаг 1: Получаем текст новостей
            news = get_latest_news(category=category_to_fetch)
            
            # Шаг 2: Если новости есть, передаем их ИИ для создания сводки
            if news:
                summary = summarize_news_with_ai(news)
                send_message(sender_id, summary)
            else:
                send_message(sender_id, f"Не удалось найти актуальные новости по категории '{category_to_fetch}'.")

        else:
            help_text = "Доступные команды:\n/news, /sport, /tech, /science, /health, /entertainment"
            send_message(sender_id, help_text)
    
    return Response(status=200)

# --- Запускаем наш сервер (без изменений) ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)