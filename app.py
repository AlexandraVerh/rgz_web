from flask import Flask
from flask import redirect, Blueprint, render_template, request, session,  abort, jsonify
import psycopg2
from psycopg2 import extras
from Db import db
from Db.models import users
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, current_user, login_required, logout_user,  login_user
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


app = Flask(__name__)
app.secret_key = '123'
user_db = 'aleksandra_rgz_web'
host_ip = '127.0.0.1'
host_port = '5432'
database_name = 'rgz_web'
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

    conn = dbConnect()
    cur = conn.cursor(cursor_factory=extras.DictCursor)
    
    # Получить все товары
    cur.execute("SELECT * FROM Furniture")
    products = cur.fetchall()

    return render_template('index.html', username=username, products=products)

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

@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():
    user_id = current_user.id

    # Удаление пользователя из базы данных
    user = users.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    logout_user()
    return redirect("/")

@app.route('/add_to_cart', methods=["POST"])
@login_required
def add_to_cart():
    product_ids = request.form.getlist("product_id")  # Get a list of product IDs
    kolvo = request.form.getlist("kolvo")  # Get a list of kolvo

    if not product_ids or not kolvo:
        abort(400)

    conn = dbConnect()
    cur = conn.cursor(cursor_factory=extras.DictCursor)

    cart_items = session.get("cart_items", [])  # Get current cart items
    cart_total = session.get("cart_total", 0)  # Get current cart total

    for product_id, qty in zip(product_ids, kolvo):
        cur.execute("SELECT name, price FROM Furniture WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if product:
            cart_item = {"name": product["name"], "price": product["price"], "qty": qty}
            cart_items.append(cart_item)
            cart_total += int(product["price"]) * int(qty)  # Update the cart total

    conn.close()
    cur.close()
    session["cart_items"] = cart_items  # Store the updated cart items
    session["cart_total"] = cart_total  # Store the updated cart total

    return render_template("cart.html", cart_items=cart_items, cart_total=cart_total)

@app.route('/remove_from_cart', methods=["POST"])
@login_required
def remove_from_cart():
    product_name = request.form.get("product_name")
    product_price = request.form.get("product_price")
    product_qty = request.form.get("product_qty")

    if not (product_name and product_price and product_qty):
        abort(400)
    
    cart_items = session.get("cart_items", [])
    updated_cart_items = []
    cart_total = session.get("cart_total", 0)  # Get current cart total
    cart_total = 0  # Initialize cart total

    for item in cart_items:
        if item["name"] != product_name or item["price"] != product_price or item["qty"] != product_qty:
            updated_cart_items.append(item)
            price = item["price"].replace(",", ".")  # Replace comma with dot as decimal separator
            cart_total += float(price) * int(item["qty"])  # Calculate total for each remaining item

    session["cart_items"] = updated_cart_items
    session["cart_total"] = cart_total  # Update the total in the session

    return redirect("/korzina")

@app.route('/korzina')
@login_required
def cart():
    
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    return render_template("cart.html", cart_items=cart_items, cart_total=cart_total)

@app.route('/oplata', methods=["GET", "POST"])
@login_required
def oplata():

    if request.method == "POST":
        # Получить данные карты из формы
        card_num = request.form.get("card_num")
        cvv = request.form.get("cvv")

        # Проверить данные карты
        if len(card_num) != 16:
            print('Неверный номер карты. Пожалуйста, введите 16-значный номер карты. ')
            return redirect('/oplata')
        
        if len(cvv) != 3:
            print('Неверный CVV. Пожалуйста, введите 3-значный CVV код. ')
            return redirect('/oplata')

        # Очистка корзины после оплаты
        session.pop("cart_items", None)
        session.pop("cart_total", None)

        return render_template('success.html')
    
    # Вывести информацию о корзине и форму оплаты
    cart_items = session.get("cart_items", [])
    cart_total = session.get("cart_total", 0)

    return render_template("oplata.html", cart_items=cart_items, cart_total=cart_total)