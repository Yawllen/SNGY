import hashlib
import re
import telebot
import config
import sqlite3
import time

salt = b"yawllen"
bot = telebot.TeleBot(config.TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Метод, запускающийся при старте бота. Принимает входящее сообщение.
    Метод проверяет: сообщение пришло боту из лс или из группы, для каждого варианта свой алгоритм действий.
    Если боту написали в лс, он переходит к методу аутентификации.
    Если боту пишут в группе:
        1. Проверка на админа.
        2. Получение информации о группе (id группы и номер проекта, по которому в БД находится id соответствующего проекта).
    """
    if(message.chat.id > 0):  #личка
        welcome(message)
    else:                   #группа
        admin = bot.get_chat_administrators(message.chat.id)
        for i in range(len(admin)):
            idAdmin = re.findall(r'\d+', str(admin[i]))
            if str(message.from_user.id) == str(idAdmin[0]):
                bot.send_message(message.chat.id, "-------Админ--------")
                chat = str(bot.get_chat(message.chat.id, ))
                splitList= re.split(r',', chat)
                splitList2 = str(splitList[2])
                title = re.findall(r"'([^'\\]*(?:\\.[^'\\]*)*)'", splitList2, re.DOTALL)
                numProj = str(re.sub(r'[^!?,.\d]+', '', str(title[1])))
                @bot.message_handler(commands=['proj'])
                def admin(message):

                    admin = bot.get_chat_administrators(message.chat.id)
                    for i in range(len(admin)):
                        idAdmin = re.findall(r'\d+', str(admin[i]))
                        if str(message.from_user.id) == str(idAdmin[0]):
                            """
                            По команде /proj бот выводит номер нашего проекта исходя из названия группы.
                            """
                            time.sleep(1)
                            bot.send_message(message.chat.id, "Номер вашего проекта: " + numProj)
                            step_Set_Project(message)
                        else:
                            bot.send_message(message.chat.id, "Вы не админ")
                def step_Set_Project(message):
                    """
                    1. Получение id проекта из БД по номеру проекта.
                    2. Заполнение id группы по id проекта в БД.
                    3. Бот выводит ссылку на себя для перехода в лс.
                    """
                    conn = sqlite3.connect('sup.sqlite')
                    cur = conn.cursor()
                    cur.execute(f"SELECT * FROM PROJ_SUP WHERE num_project = '{numProj}'")
                    record1 = cur.fetchone()
                    if record1:
                        idProj = str(record1[0])
                        bot.send_message(message.chat.id, "ID вашего проекта: " + idProj)
                        conn = sqlite3.connect('db_proj.db')
                        cur = conn.cursor()
                        cur.execute(f"SELECT * FROM GROUPP WHERE id_project  = '{idProj}'")
                        record2 = cur.fetchone()
                        if record2:
                            if record2[1]:
                                # bot.send_message(message.chat.id, "Обновление данных")
                                cur.execute(
                                    f"UPDATE GROUPP SET id_group  = '{message.chat.id}' WHERE id_project  = '{idProj}' ")
                                conn.commit()
                            else:
                                cur.close()
                        else:
                            cur.close()

                        time.sleep(1)
                        bot.send_message(message.chat.id, "@PractInSynerBot")

                    else:
                        cur.close()
                        time.sleep(1)
                        bot.send_message(message.chat.id, "Записи не найдены")
            else:
                bot.send_message(message.chat.id, "Вы не админ")
def welcome(message):
    """
    Приветствие и аутентификация пользователя в лс
    """
    name = message.from_user.first_name
    secondName = message.from_user.last_name
    if secondName is not None:
        bot.send_message(message.chat.id, "Здравствуйте, " + name + " " + secondName + "! ")
        time.sleep(1)
        bot.send_message(message.chat.id, "Для того, чтобы получать и отправлять сообщения, нужно произвести авторизацию на сайте.")
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
    """
    Проверка логина пользователя и ввод пароля
    """
    global userLogin
    userLogin = message.text
    time.sleep(1)
    password = bot.send_message(message.chat.id, "Введите пароль")
    bot.register_next_step_handler(password, step_Set_Password)

def step_Set_Password(message):
    """
    Хеширование пароля с солью
    """
    global key
    key = hashlib.pbkdf2_hmac('sha256', message.text.encode('utf-8'), salt, 100000)
    check(message)

def check(message):
    """
    Проверка введённых данных пользователя по данным СУП.
    Если проверка прошла успешно:
        1. Приветствие пользователя по его имени из СУП.
        2. Вывод id пользователя из СУП.
        3. Сравниваем id пользователя из СУП с id пользователя из БД.
        4. Если такой записи нет в БД, добавляем её.
    Если проверка не пройдена, пользователя просят ввести данные повторно.
    """
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
                    bot.send_message(message.chat.id, "Авторизация прошла успешно!")
                    cur.close()
                else:
                    time.sleep(1)
                    bot.send_message(message.chat.id, "Авторизация прошла успешно!")
                    cur.close()
            else:
                cur.close()
                time.sleep(1)
                bot.send_message(message.chat.id, "Логин или пароль неверный")
                send_welcome(message)
        else:
            cur.close()
            time.sleep(1)
            bot.send_message(message.chat.id, "Логин или пароль неверный")
            send_welcome(message)
    else:
        cur.close()
        time.sleep(1)
        bot.send_message(message.chat.id, "Логин или пароль неверный")
        send_welcome(message)


bot.polling(none_stop=True)