from flask import Flask
from flask import redirect, Blueprint, render_template, request, session
import psycopg2
from Db import db
from Db.models import users
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, current_user, login_required, logout_user,  login_user
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


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
def load_user(user_id):
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

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_users(user_id):
    return users.query.get(int(user_id))


@app.route('/')
def glavnaya():
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = "Аноним"

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
    return render_template('index.html', username=username, categorized_products=categorized_products, categories=categories)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username_form = request.form.get("username")
    password_form = request.form.get("password")

    # Проверка пустого имени пользователя
    if not username_form:
        error = "Пустое имя!"
        return render_template("register.html", error=error)

    # Проверка длины пароля
    if len(password_form) < 5:
        error = "Пароль должен содержать не менее 5 символов!"
        return render_template("register.html", error=error)

    # Проверка наличия пользователя с таким именем
    existing_user = users.query.filter_by(username=username_form).first()
    if existing_user:
        error = "Пользователь с таким именем уже существует!"
        return render_template("register.html", error=error)

    # Создание нового пользователя
    hashed_password = generate_password_hash(password_form, method="pbkdf2")
    new_user = users(username=username_form, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username_form = request.form.get("username")
    password_form = request.form.get("password")

    if not username_form or not password_form:
        error = "Поле имя и/или пароль не заполнено"
        return render_template("login.html", error=error)

    my_user = users.query.filter_by(username=username_form).first()

    if my_user is None:
        error = "Пользователь не существует"
        return render_template("login.html", error=error)

    if not check_password_hash(my_user.password, password_form):
        error = "Неправильный пароль"
        return render_template("login.html", error=error)

    login_user(my_user, remember=False)
    return redirect("/")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/add_to_cart", methods=["POST"])
@login_required
def addToCart():
    product_ids = request.form.getlist("product_id")  # Получаем список идентификаторов товаров из формы
    if "cart" not in session:
        session["cart"] = []
    session["cart"].extend(product_ids)  # Добавляем все идентификаторы в корзину
    return redirect("/")

@app.route("/cart")
@login_required
def viewCart():
    cart_items = session.get("cart", [])
    products = []
    if cart_items:
        conn = dbConnect()
        cur = conn.cursor()
        # Получить информацию о товарах в корзине из базы данных
        for cart_item in cart_items:
            cur.execute("SELECT name, price FROM furniture WHERE name = %s;", (cart_item,))
            result = cur.fetchone()
            if result:
                name, price = result
                products.append({
                    "name": name,
                    "price": price
                })
        dbClose(cur, conn)
    return render_template("cart.html", products=products)

@app.route("/remove_from_cart", methods=["POST"])
@login_required
def removeFromCart():
    name = request.form.get("name")
    cart_items = session.get("cart", [])
    if name in cart_items:
        cart_items.remove(name)
    return redirect("/cart")

