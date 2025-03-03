import telebot
from telebot import types
import sqlite3
import json

# Замените токен на свой
bot = telebot.TeleBot("8111134301:AAEOCtAfXjwN9GPXInvqAoPel8RP962FIYQ")

# --- Подключение к базе данных (SQLite) ---
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    score INTEGER DEFAULT 0
)
''')
conn.commit()

def register_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (id, username, score) VALUES (?, ?, ?)", (user_id, username, 0))
        conn.commit()

def update_score(user_id, additional_points):
    cursor.execute("SELECT score FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        new_score = result[0] + additional_points
        cursor.execute("UPDATE users SET score = ? WHERE id = ?", (new_score, user_id))
        conn.commit()

def get_ratings():
    cursor.execute("SELECT username, score FROM users ORDER BY score DESC LIMIT 10")
    return cursor.fetchall()

# --- Функция для создания клавиатуры выбора игр ---
def get_games_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Создаем кнопки Web App для мини-приложений
    english_web_app = types.WebAppInfo(url="file:///C:/Users/julia/Desktop/ThreeInOneGames_bot/english_game.html")  # URL мини-приложения для игры "Английский"
    flappy_web_app = types.WebAppInfo(url="https://yourdomain.com/flappy_birds")   # URL для Flappy Birds
    pingpong_web_app = types.WebAppInfo(url="https://yourdomain.com/ping_pong")      # URL для Ping-Pong
    
    btn_english = types.KeyboardButton("Игра: Английский", web_app=english_web_app)
    btn_flappy = types.KeyboardButton("Flappy Birds", web_app=flappy_web_app)
    btn_pingpong = types.KeyboardButton("Ping-Pong", web_app=pingpong_web_app)
    
    # Для рейтинга можно оставить обычную кнопку, обработка которой происходит в боте
    btn_rating = types.KeyboardButton("Рейтинг")
    
    markup.add(btn_english, btn_flappy, btn_pingpong, btn_rating)
    return markup

# --- Обработчик команды /start ---
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id, message.from_user.username)
    bot.send_message(message.chat.id,
                     "Добро пожаловать! Выберите игру или просмотрите рейтинг:",
                     reply_markup=get_games_markup())

# --- Основной обработчик текстовых сообщений ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.strip()
    
    if text == "Рейтинг":
        ratings = get_ratings()
        if ratings:
            rating_text = "Общий рейтинг:\n"
            for i, (username, score) in enumerate(ratings, 1):
                rating_text += f"{i}. {username} - {score} очков\n"
        else:
            rating_text = "Рейтинг пока пуст."
        bot.send_message(message.chat.id, rating_text)
    else:
        bot.send_message(message.chat.id, "Выберите игру из меню или просмотрите рейтинг.")

# --- Обработчик данных, полученных из мини-приложений ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    # Получаем данные, отправленные из мини-приложения
    data = message.web_app_data.data  # Ожидается, что данные будут в формате JSON
    bot.send_message(message.chat.id, f"Получены данные из мини-приложения: {data}")
    
    try:
        result = json.loads(data)
        # Пример ожидаемой структуры: {"game": "english", "score": 10}
        if result.get("game") == "english" and "score" in result:
            update_score(message.from_user.id, result["score"])
            bot.send_message(message.chat.id, f"Ваш счёт обновлён на {result['score']} очков.")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обработке данных из мини-приложения.")

bot.polling(none_stop=True, interval=0)
