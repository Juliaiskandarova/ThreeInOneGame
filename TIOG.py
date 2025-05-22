# bot.py
import telebot
from telebot import types
import sqlite3
import json

API_TOKEN = "8111134301:AAGARPiSiNLsIaa32I93fWCAJ-F5crKmTvk"
bot = telebot.TeleBot(API_TOKEN)

# Подключение к БД
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
    cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (id, username, score) VALUES (?, ?, 0)",
            (user_id, username)
        )
        conn.commit()


def update_score(user_id, additional_points):
    # получаем старый счет
    cursor.execute("SELECT score FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    old = row[0] if row else 0
    new = old + additional_points
    cursor.execute("UPDATE users SET score = ? WHERE id = ?", (new, user_id))
    conn.commit()


def get_ratings():
    cursor.execute(
        "SELECT username, score FROM users ORDER BY score DESC LIMIT 10"
    )
    return cursor.fetchall()

def get_games_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Web App для английской игры
    english_web = types.WebAppInfo(
        url="https://juliaiskandarova.github.io/ThreeInOneGame/english_game.html"
    )
    btn_eng = types.KeyboardButton("📝 Английский", web_app=english_web)
    # Пусть в будущем добавим другие мини-игры
    btn_rating = types.KeyboardButton("🏆 Рейтинг")
    markup.add(btn_eng, btn_rating)
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
    if message.text == "🏆 Рейтинг":
        ratings = get_ratings()
        if ratings:
            txt = "⭐️ Топ игроков ⭐️\n\n"
            for i, (user, sc) in enumerate(ratings, 1):
                txt += f"{i}. {user} — {sc} очков\n"
        else:
            txt = "Рейтинг пока пуст."
        bot.send_message(message.chat.id, txt)
    else:
        bot.send_message(
            message.chat.id,
            "Нажмите кнопку игры или «🏆 Рейтинг»."
        )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    data = message.web_app_data.data
    try:
        result = json.loads(data)
    except json.JSONDecodeError:
        return bot.send_message(message.chat.id, "Неверный формат данных от WebApp.")

    if "score" not in result or "game" not in result:
        return bot.send_message(message.chat.id, "Нет данных по очкам.")

    user_id = message.from_user.id
    score = result["score"]
    game = result["game"]

    # Сохраняем именно лучший рекорд
    update_score(user_id, score)
    session_points = result["score"]
    game = result["game"]
   # Накопим к общей сумме
    update_score(user_id, session_points)

    if game == "english":
        text = f"Вы завершили игру «Английский». Ваш лучший рекорд – {score} очков!"
    elif game == "snake":
        text = f"Вы завершили «Змейку». Ваш лучший рекорд – {score} очков!"
    else:
        text = f"Игра «{game}» завершена. Результат – {score}."

    bot.send_message(message.chat.id, text)

if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
