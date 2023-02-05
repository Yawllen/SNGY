import hashlib
import telebot
import config
import sqlite3
import time


salt = b"yawllen"
bot = telebot.TeleBot(config.TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if(message.chat.id > 0):  #личка
        welcome(message)
    else:                   #группа
        if message.from_user.id == 623505995: # тут нужны свои id админов
            bot.send_message(message.chat.id, "Админ")
            @bot.message_handler(commands=['proj'])
            def admin(message):
                time.sleep(1)
                numProj = bot.send_message(message.chat.id, 'Введите номер проекта')
                bot.register_next_step_handler(numProj, step_Set_Project)
            def step_Set_Project(message):
                adminProj = message.text
                conn = sqlite3.connect('sup.sqlite')
                cur = conn.cursor()
                bot.send_message(message.chat.id, "Вы ввели: " + adminProj)
                cur.execute(f"SELECT * FROM PROJ_SUP WHERE num_project = '{adminProj}'")
                record1 = cur.fetchone()
                bot.send_message(message.chat.id, record1)
                if record1:
                    idProj = str(record1[0])
                    bot.send_message(message.chat.id, "ID проекта: " + idProj)
                    conn = sqlite3.connect('db_proj.db')
                    cur = conn.cursor()
                    cur.execute(f"SELECT * FROM GROUPP WHERE id_project  = '{idProj}'")
                    record2 = cur.fetchone()
                    if record2:
                        bot.send_message(message.chat.id, "Запись не пустая")
                        if record2[1] is None:
                            # bot.send_message(message.chat.id, "Обновление данных")
                            cur.execute(f"UPDATE GROUPP SET  id_group  = '{message.chat.id}' WHERE id_project  = '{idProj}' ")
                            conn.commit()
                        else:
                            # bot.send_message(message.chat.id, "Выход 1")
                            cur.close()
                    else:
                        # bot.send_message(message.chat.id, "Выход 2")
                        cur.close()

                    time.sleep(1)
                    bot.send_message(message.chat.id, "@PractInSynerBot")

                else:
                    cur.close()
                    time.sleep(1)
                    bot.send_message(message.chat.id, "Записи не найдены")
                    admin(message)

def welcome(message):
    name = message.from_user.first_name
    secondName = message.from_user.last_name
    if secondName is not None:
        bot.send_message(message.chat.id, "Здравствуйте, " + name + " " + secondName + "! ")
        time.sleep(1)
        bot.send_message(message.chat.id, "Для того, чтобы получать и отправлять сообщения, нужно провести аутентификацию на сайте.")
        time.sleep(1)
        login = bot.send_message(message.chat.id, 'Введите логин')
        bot.register_next_step_handler(login, step_Set_Login)
    else:
        bot.send_message(message.chat.id, "Привет, " + name + "! ")
        time.sleep(1)
        bot.send_message(message.chat.id, "Для того, чтобы получать и отправлять сообщения, нужно провести аутентификацию на сайте.")
        time.sleep(1)
        login = bot.send_message(message.chat.id, 'Введите логин')
        bot.register_next_step_handler(login, step_Set_Login)

def step_Set_Login(message):
    global userLogin
    userLogin = message.text
    time.sleep(1)
    password = bot.send_message(message.chat.id, "Введите пароль")
    bot.register_next_step_handler(password, step_Set_Password)

def step_Set_Password(message):
    global key
    key = hashlib.pbkdf2_hmac('sha256', message.text.encode('utf-8'), salt, 100000)
    # bot.send_message(message.chat.id, "Ваш пароль: " + password)
    check(message)

def check(message):
    loginForCheck = str(userLogin)
    conn = sqlite3.connect('sup.sqlite')
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM AUTH WHERE login = '{loginForCheck}'")
    record = cur.fetchone()
    if record:
        if record[1] == loginForCheck:
            if record[2] == str(key):
                time.sleep(1)
                bot.send_message(message.chat.id, "Добро пожаловать, " + record[3] + '!')
                time.sleep(1)
                bot.send_message(message.chat.id, "Ваш ID: " + str(record[0]))
                userID = str(record[0])
                conn = sqlite3.connect('db_proj.db')
                cur = conn.cursor()
                cur.execute(f"SELECT id_user FROM CHAT WHERE id_user = '{userID}'")
                eq = cur.fetchone()
                if eq is None:
                    cur.execute(f"INSERT INTO CHAT (id_user, id_chat)  VALUES (?, ?)", (userID, message.chat.id))
                    conn.commit()
                    time.sleep(1)
                    bot.send_message(message.chat.id, "Авторизация прошла успешно 1!")
                    cur.close()
                else:
                    time.sleep(1)
                    bot.send_message(message.chat.id, "Авторизация прошла успешно 2!")
                    cur.close()
            else:
                cur.close()
                time.sleep(1)
                bot.send_message(message.chat.id, "Логин или пароль неверный 1")
                send_welcome(message)
        else:
            cur.close()
            time.sleep(1)
            bot.send_message(message.chat.id, "Логин или пароль неверный 2")
            send_welcome(message)
    else:
        cur.close()
        time.sleep(1)
        bot.send_message(message.chat.id, "Логин или пароль неверный 3")
        send_welcome(message)


bot.polling(none_stop=True)