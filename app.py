from flask import Flask
from flask import redirect, Blueprint, render_template, request, session
import psycopg2
from Db import db
from Db.models import users
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import current_user
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

app = Flask(__name__)
app.secret_key = '123'
user_db = 'aleksandra_rgz_web_orm'
host_ip = '127.0.0.1'
host_port = '5432'
database_name = 'rgz_web_orm'
password = '1235'

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_users(user_id):
    return users.query.get(int(user_id))

def dbConnect(): 
    conn = psycopg2.connect( 
        host="127.0.0.1", 
        database = "rgz_web", 
        user = "aleksandra_rgz_web", 
        password = "1235") 
 
    return conn; 
 
def dbClose(cursor,connection): 
    #закрываем курсор и соединение. порядок важен
    cursor.close() 
    connection.close()

@app.route("/") 
def main(): 
    visibleUser = session.get('username', 'Anon') 
    # Прописываем параметры подключения к БД 
    conn = psycopg2.connect( 
        host="127.0.0.1", 
        database="rgz_web", 
        user="aleksandra_rgz_web", 
        password="1235", 
        port = 5432
    ) 
    # Получаем курсор. С помощью него мы можем выполнять SQL-запросы 
    cur = conn.cursor() 
    # Пишем запрос, который курсор должен выполнить 
    cur.execute("SELECT * FROM users;") 
    # fetchall - получить все строки, которые получились в результате выполнения SQL-запроса в execute 
    # Сохраняем эти строки в переменную result 
    result = cur.fetchall() 
    
    # Открытие файла изображения и чтение его в формате BYTEA
    

    cur = conn.cursor()
    cur.execute("SELECT name, category, price, description FROM furniture ORDER BY category;")
    products = cur.fetchall()

    cur.close() 
    conn.close() 

    print(result) 

    categories = set([product[1] for product in products])  # Получаем уникальные категории товаров

    categorized_products = {}  # Создаем словарь, где ключи - это категории, значения - списки товаров в каждой категории

    # Группируем товары по категориям
    for product in products:
        category = product[1]
        if category in categorized_products:
            categorized_products[category].append(product)
        else:
            categorized_products[category] = [product]

    return render_template('index.html', username=visibleUser, categorized_products=categorized_products, categories=categories)
 


@app.route('/register', methods=['GET', 'POST'])
def registerPage():
    error = ''

    if request.method == 'GET':
        return render_template('register.html', error=error)

    username = request.form.get('username')
    password = request.form.get('password')

    if not (username and password):
        error="Пожалуйста, заполните все поля"
        print(error)
        return render_template('register.html', error=error)

    hashPassword = generate_password_hash(password)

    conn = dbConnect()
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM users WHERE username = '{username}';")

    if cur.fetchone() is not None:#не получаем ббольше одной строки только один пользователь может быть с таким именем
        error = "Пользователь с данным именем уже существует"

        dbClose(cur, conn)
        return render_template('register.html', error=error)
    
    #сохраняем пароль в вижде хэша в бд
    cur.execute(f"INSERT INTO users (username, password) VALUES ('{username}','{hashPassword}');")
    conn.commit()#фиксируем изменения
    dbClose(cur, conn)

    return redirect("/login")

@app.route('/login', methods=['GET', 'POST'])
def loginPage():
    error = ''

    if request.method == 'GET':
        return render_template('login.html', error=error)

    username = request.form.get('username')
    password = request.form.get('password')

    if not (username and password):
        error="Пожалуйста, заполните все поля"
        return render_template('login.html', error=error)

    conn = dbConnect()
    cur = conn.cursor()
    cur.execute(f"SELECT id, password FROM users WHERE username = '{username}'")
    result = cur.fetchone()

    if result is None:
        error="Неправильный логин или пароль"
        dbClose(cur,conn)  # Закрытие соединения
        return render_template('login.html', error=error)
    
    userID, hashPassword = result
    if check_password_hash(hashPassword, password):
        session['id'] = userID
        session['username'] = username
        dbClose(cur,conn)  # Закрытие соединения
        return redirect("/")
    else:
        error ="Неправильный логин или пароль"
        return render_template("login.html", error=error)
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")