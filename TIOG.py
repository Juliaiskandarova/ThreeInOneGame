import telebot
from telebot import types
import sqlite3
import json

bot = telebot.TeleBot("8111134301:AAEOCtAfXjwN9GPXInvqAoPel8RP962FIYQ")


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


def get_games_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    english_web_app = types.WebAppInfo(url="https://juliaiskandarova.github.io/ThreeInOneGame/english_game.html")
    
    btn_english = types.KeyboardButton("Игра: Английский", web_app=english_web_app)
    btn_rating = types.KeyboardButton("Рейтинг")

    # чтобы не вызывать ошибку
    # flappy_web_app = types.WebAppInfo(url="https://YOUR_DOMAIN/flappy_birds.html")
    # pingpong_web_app = types.WebAppInfo(url="https://YOUR_DOMAIN/ping_pong.html")
    # btn_flappy = types.KeyboardButton("Flappy Birds", web_app=flappy_web_app)
    # btn_pingpong = types.KeyboardButton("Ping-Pong", web_app=pingpong_web_app)
    
    # markup.add(btn_english, btn_flappy, btn_pingpong, btn_rating)
    markup.add(btn_english, btn_rating)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id, message.from_user.username)
    bot.send_message(
        message.chat.id,
        "Добро пожаловать! Выберите игру или просмотрите рейтинг:",
        reply_markup=get_games_markup()
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.strip()
    
    if text == "Рейтинг":
        ratings = get_ratings()
        if ratings:
            rating_text = "⭐️ Топ игроков ⭐️\n\n"
            for i, (username, score) in enumerate(ratings, 1):
                rating_text += f"{i}. {username} — {score} очков\n"
        else:
            rating_text = "Рейтинг пока пуст."
        bot.send_message(message.chat.id, rating_text)
    else:
        bot.send_message(message.chat.id, "Выберите игру из меню или просмотрите рейтинг.")

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    bot.send_message(message.chat.id, "Обрабатываю результат игры...")
    try:
        data = message.web_app_data.data
        result = json.loads(data)
        
        if result.get("game") == "english" and "score" in result:
            update_score(message.from_user.id, result["score"])
            total_score = result["score"]
            bot.send_message(
                message.chat.id,
                f"Вы завершили игру по английскому языку и набрали {total_score} очков!"
            )
        else:
            bot.send_message(message.chat.id, "Результат получен, но не распознан как английская игра.")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка при обработке данных из мини-приложения.")

bot.polling(none_stop=True, interval=0)
