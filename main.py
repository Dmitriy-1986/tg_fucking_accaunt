import os
from flask import Flask, request, render_template, redirect, url_for, session
from telethon import TelegramClient
from dotenv import load_dotenv
import asyncio

# Загружаем переменные окружения из .env файла
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Получаем API ID и API Hash из переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# Проверка наличия необходимых переменных окружения
if not API_ID or not API_HASH:
    raise ValueError("API_ID и API_HASH должны быть установлены в .env файле")

# Создаем глобальный цикл событий
loop = asyncio.get_event_loop()

# Используем файловую сессию для сохранения авторизации
client = TelegramClient("session_name", API_ID, API_HASH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    phone_number = request.form['phone'].strip()
    session['phone_number'] = phone_number  # Сохраняем номер телефона в сессии

    try:
        # Отправляем код в асинхронной функции
        loop.run_until_complete(login_and_send_code(phone_number))
        return redirect(url_for('verify'))
    except Exception as e:
        print(f"Ошибка при отправке кода: {e}")
        return f"Ошибка при отправке кода: {e}"

async def login_and_send_code(phone_number):
    try:
        await client.connect()
        await client.send_code_request(phone_number)
        print(f"Код отправлен на номер: {phone_number}")
    except Exception as e:
        print(f"Ошибка при отправке кода: {e}")
        raise e

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form['code'].strip()
        phone_number = session.get('phone_number')

        try:
            result = loop.run_until_complete(verify_code(phone_number, code))
            if result == "two_factor":
                return redirect(url_for('password'))
            elif result == "success":
                return "Успешно вошли в аккаунт!"
            else:
                return f"Ошибка авторизации: {result}"
        except Exception as e:
            print(f"Ошибка при подтверждении кода: {e}")
            return f"Ошибка при подтверждении кода: {e}"

    return render_template('verify.html')

async def verify_code(phone_number, code):
    try:
        await client.connect()
        await client.sign_in(phone_number, code)
        return "success"
    except Exception as e:
        if 'Two-step verification' in str(e):
            print("Требуется ввод пароля для двухфакторной аутентификации.")
            return "two_factor"
        else:
            return str(e)

@app.route('/password', methods=['GET', 'POST'])
def password():
    if request.method == 'POST':
        password = request.form['password'].strip()
        phone_number = session.get('phone_number')

        try:
            result = loop.run_until_complete(verify_password(phone_number, password))
            if result == "success":
                return "Успешно вошли в аккаунт с двухфакторной аутентификацией!"
            else:
                return f"Ошибка при вводе пароля: {result}"
        except Exception as e:
            print(f"Ошибка при вводе пароля: {e}")
            return f"Ошибка при вводе пароля: {e}"

    return render_template('password.html')

async def verify_password(phone_number, password):
    try:
        await client.sign_in(phone_number, password=password)
        return "success"
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    loop.run_until_complete(client.connect())  # Подключаем клиента при старте приложения
    app.run(debug=True)