import hashlib
import telebot
import config
import sqlite3


salt = b"yawllen"
bot = telebot.TeleBot(config.TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет, " + message.from_user.username + "! ")
    bot.send_message(message.chat.id, "Для того, чтобы получать и отправлять сообщения, нужно провести аутентификацию на сайте.")
    login = bot.send_message(message.chat.id, 'Введите логин')
    bot.register_next_step_handler(login, step_Set_Login)

def step_Set_Login(message):
    global userLogin
    userLogin= message.text
    bot.send_message(message.chat.id, "Ваш логин: " + userLogin)
    password = bot.send_message(message.chat.id, "Введите пароль")
    bot.register_next_step_handler(password, step_Set_Password)

def step_Set_Password(message):
    global key
    key = hashlib.pbkdf2_hmac('sha256', message.text.encode('utf-8'), salt, 100000)
    # bot.send_message(message.chat.id, "Ваш пароль: " + password)
    check(message)

@bot.message_handler(commands=['Link'])
def send_link(message):
    bot.send_message(message.chat.id, "@PractInSynerBot")

def check(message):

        loginForCheck = str(userLogin)

        # bot.send_message(message.chat.id, "userLogin:  " + loginForCheck)
        conn = sqlite3.connect('sup.sqlite')
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM AUTH WHERE login = '{loginForCheck}'")
        record = cur.fetchone()
        if record:
            if record[1] == loginForCheck:
                if record[2] == str(key):
                    bot.send_message(message.chat.id, "Добро пожаловать, " + record[3] + '!')
                    bot.send_message(message.chat.id, "Ваш ID: " + str(record[0]))
                else:
                    cur.close()
                    bot.send_message(message.chat.id, "Логин или пароль неверный 1")
                    send_welcome(message)
            else:
                cur.close()
                bot.send_message(message.chat.id, "Логин или пароль неверный 2")
                send_welcome(message)
        else:
            cur.close()
            bot.send_message(message.chat.id, "Логин или пароль неверный 3")
            send_welcome(message)


bot.polling(none_stop=True)