from flask import Flask
from flask import redirect, Blueprint, render_template, request, session,  abort
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

@app.route('/add_to_cart', methods=["POST"])
@login_required
def add_to_cart():
     
    product_ids = request.form.getlist("product_id")  # Get a list of product IDs
    kolvo = request.form.getlist("kolvo")     # Get a list of kolvo

    if not product_ids or not kolvo:
        abort(400)

    # Add the products and kolvo to the cart
    # cart_items = []
    # for product_id, kolvo in zip(product_ids, kolvo):
    #     cart_items.append({"product_id": product_id, "kolvo": kolvo})

    # return render_template("korzina.html", cart_items=cart_items)
    conn = dbConnect()
    cur = conn.cursor(cursor_factory=extras.DictCursor)

    cart_items = []
    for product_id, kolvo in zip(product_ids, kolvo):
        cur.execute("SELECT name, price FROM Furniture WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if product:
            cart_items.append({"name": product["name"], "price": product["price"], "kolvo": kolvo})

    conn.close()
    cur.close()
    session["cart_items"] = cart_items

    return render_template("cart.html", cart_items=cart_items)

@app.route('/korzina')
@login_required
def cart():
    
    cart_items = session.get("cart_items", [])

    return render_template("cart.html", cart_items=cart_items)

