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
        if 'Two-steps verification' in str(e):
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