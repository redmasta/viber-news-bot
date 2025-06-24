import requests
import json
import os
import google.generativeai as genai
from flask import Flask, request, Response
import threading # <-- Импортируем новую библиотеку для потоков

# --- Инициализация и константы (без изменений) ---
app = Flask(__name__)
VIBER_AUTH_TOKEN = os.environ.get("VIBER_AUTH_TOKEN")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Все вспомогательные функции (get_latest_news, summarize_news_with_ai, create_main_keyboard, send_message) остаются БЕЗ ИЗМЕНЕНИЙ ---
# (Я их здесь опущу для краткости, но в вашем файле они должны остаться как есть)

def get_latest_news(category='general'):
    # ... ваш код ...
    pass

def summarize_news_with_ai(news_text):
    # ... ваш код ...
    pass

def create_main_keyboard():
    # ... ваш код ...
    pass

def send_message(receiver_id, text, keyboard=None):
    # ... ваш код ...
    pass

# --- НОВАЯ ФУНКЦИЯ, КОТОРАЯ БУДЕТ РАБОТАТЬ В ФОНЕ ---
def process_news_request_in_background(sender_id, category_to_fetch):
    """Эта функция выполняет всю долгую работу в отдельном потоке."""
    print(f"Фоновый поток запущен для пользователя {sender_id}, категория: {category_to_fetch}")
    
    # Сначала отправляем пользователю сообщение, что мы начали работать
    send_message(sender_id, f"Ищу новости по категории '{category_to_fetch}' и подключаю ИИ-аналитика...")
    
    # Шаг 1: Получаем новости
    news = get_latest_news(category=category_to_fetch)
    
    # Шаг 2: Если новости есть, передаем их ИИ
    if news:
        summary = summarize_news_with_ai(news)
        # Шаг 3: Отправляем финальный результат
        send_message(sender_id, summary)
    else:
        send_message(sender_id, f"Не удалось найти актуальные новости по категории '{category_to_fetch}'.")
    
    print(f"Фоновый поток для пользователя {sender_id} завершил работу.")


# --- ОБНОВЛЕННАЯ ГЛАВНАЯ ЛОГИКА БОТА ---
@app.route('/', methods=['POST'])
def incoming():
    viber_request = request.get_json()
    print(f"\n--- Получен новый запрос от Viber ---\n{viber_request}")

    if viber_request.get('event') == 'message':
        sender_id = viber_request['sender']['id']
        message_text = viber_request['message']['text'].lower()
        
        category_to_fetch = None
        
        if message_text in ["/news", "/general"]: category_to_fetch = "general"
        elif message_text == "/politics": category_to_fetch = "politics"
        elif message_text == "/tech": category_to_fetch = "technology"
        elif message_text == "/sport": category_to_fetch = "sports"
        elif message_text == "/science": category_to_fetch = "science"
        elif message_text == "/health": category_to_fetch = "health"
        
        if category_to_fetch:
            # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ---
            # Мы не ждем выполнения всей работы.
            # Мы создаем и запускаем отдельный поток, который всем займется.
            # А сами СРАЗУ ЖЕ отвечаем Viber "OK".
            thread = threading.Thread(target=process_news_request_in_background, args=(sender_id, category_to_fetch))
            thread.start()
        else:
            # Отправка меню с кнопками - быстрая операция, ее можно оставить здесь
            help_text = "Привет! Я новостной бот-аналитик Trumper. Выберите категорию для получения сводки и анализа:"
            main_keyboard = create_main_keyboard()
            send_message(sender_id, help_text, main_keyboard)
    
    # Отвечаем Viber статус 200 OK МГНОВЕННО
    return Response(status=200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
