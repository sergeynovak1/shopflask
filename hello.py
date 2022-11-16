import datetime
import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from db_util import Database
from UserLogin import UserLogin


def page_not_found(e):
    return redirect(url_for('products'))


app = Flask(__name__, static_folder='./static')

UPLOAD_FOLDER = f'C:\\Users\\novak\\PycharmProjects\\shopflask\\static\\images\\'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.secret_key = '111'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.register_error_handler(404, page_not_found)

app.permanent_session_lifetime = datetime.timedelta(days=365)

db = Database()

login_manager = LoginManager(app)





@login_manager.user_loader
def load_user(user_id):
    #print("load_user")
    return UserLogin().fromDB(user_id, db)


@app.route('/', methods=['GET', 'POST'])
def products():
    categories = db.execute_list(f"SELECT distinct category FROM ad")
    try:
        role = db.execute(f"select role from users where id='{session['_user_id']}'")['role']
    except:
        role = None
    list_categories = ['Без категории']
    for category in categories:
        list_categories.append(category['category'])
    name = request.form.get('name') if request.form.get('name') else ''
    category = str(request.form.get('category')) if request.form.get('category') else ''
    category_n = tuple(list_categories[1:]) if category=='Без' else [category]
    if category and name:
        if len(category_n) > 1:
            products = db.execute_list(f"SELECT * FROM ad WHERE category in {category_n} and name='{name}'")
        else:
            products = db.execute_list(f"SELECT * FROM ad WHERE category='{category_n[0]}' and name='{name}'")
    elif category:
        if len(category_n) > 1:
            products = db.execute_list(f"SELECT * FROM ad WHERE category in {category_n}")
        else:
            products = db.execute_list(f"SELECT * FROM ad WHERE category='{category_n[0]}'")
    elif name:
        products = db.execute_list(f"SELECT * FROM ad WHERE name='{name}'")
    else:
        products = db.execute_list(f"SELECT * FROM ad")
    context = {
        'products': products,
        'title': "PRODUCTS",
        'p_category': category,
        'name': name,
        'categories': list_categories,
        'role': role,
    }
    return render_template("products.html", **context)


@app.route("/product/<int:product_id>")
def get_product(product_id):
    try:
        role = db.execute(f"select role from users where id='{session['_user_id']}'")['role']
        product = db.execute(f"select id, name, price, description, category, image from ad where id='{product_id}'")
        if db.execute_list(f"SELECT * FROM fav WHERE productid = {product_id} and userid = {session['_user_id']}") == []:
            in_fav = False
        else:
            in_fav = True
        return render_template("product.html", title=product['name'], product=product, role=role, in_fav=in_fav)
    except:
        try:
            product = db.execute(
                f"select id, name, price, description, category, image from ad where id='{product_id}'")
            return render_template("product.html", title=product['name'], product=product, role=None)
        except:
            return render_template("error.html", error="Такого товара не существует")


@app.route("/register", methods=["POST", "GET"])
def register():
    prof = {'id': '', 'email': ''}
    if request.method == "POST":
        emails = db.execute_list(f"SELECT email FROM users")
        list_emails = []
        for email in emails:
            list_emails.append(email['email'])
        if len(request.form['email']) > 4 and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2'] and request.form['email'] not in list_emails:
            hash = generate_password_hash(request.form['psw'])
            db.insert(f"INSERT INTO users values (default, '{request.form['email']}', '{hash}', 'user');")
            flash("Вы успешно зарегистрированы")
            return redirect(url_for('login'))
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("registration.html", title="Регистрация", prof=prof)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = db.getUserByEmail(request.form['email'])
        if user and check_password_hash(user[2], request.form['psw']):
            userlogin = UserLogin().create(user)
            login_user(userlogin)
            session['user_name'] = request.form['email']
            return redirect(url_for('products'))
        flash("Неверный логин или пароль", "error")
    return render_template("login.html", title="Авторизация")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route("/addToCart", methods=["POST", "GET"])
def addToCart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    print(productId, userId)
    try:
        quan_f = int(request.form['quan'])
        db.insert(f"UPDATE kart SET quantity={quan_f} WHERE userid={userId} and productid={productId}")
        print(111)
    except:
        try:
            print(db.execute(f"SELECT quantity FROM kart WHERE userid={userId} and productid={productId}"))
            quan = db.execute(f"SELECT quantity FROM kart WHERE userid={userId} and productid={productId}")[
                'quantity']
            db.insert(f"UPDATE kart SET quantity={quan}+1 WHERE userid={userId} and productid={productId}")

            print(222)

            msg = "Added successfully"
        except:
            db.insert(f"INSERT INTO kart (userid, productid, quantity) VALUES ({userId}, {productId}, 1)")
            msg = "Error occured"
            print(444)
    flash("Товар добавлен в корзину")
    return redirect(url_for('cart'))


@app.route("/cart")
def cart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    userId = session['_user_id']
    products = db.execute_list(f"SELECT ad.id, ad.name, ad.price, kart.quantity, ad.image FROM ad JOIN kart ON ad.id = kart.productId WHERE kart.userId = {userId};")
    totalPrice = 0
    products_id_p = db.execute_list(f"SELECT productId FROM kart WHERE kart.userId = {userId}")
    products_id = []
    for row in products_id_p:
        products_id.append(row['productid'])
    session['products'] = products_id
    for row in products:
        totalPrice += row['price']*row['quantity']
    return render_template("cart.html", products=products, title='Корзина', totalPrice=totalPrice)


@app.route("/removeFromCart")
def removeFromCart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        db.insert(f"DELETE FROM kart WHERE userId = {userId} AND productId = {productId}")
        flash("Товар удален из корзины")
    except:
        flash("Ошибка", 'error')
    return redirect(url_for('cart'))


@app.route("/addToFav")
def addToFav():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        if db.execute_list(f"SELECT * FROM fav WHERE productid = {productId} and userid = {userId}") == []:
            db.insert(f"INSERT INTO fav (userId, productId) VALUES ({userId}, {productId})")
            flash("Товар добавлен в избранное")
        else:
            flash("Товар уже в избранном")
    except:
        flash("Ошибка авторизации", 'error')
    return redirect(url_for('products'))


@app.route("/fav")
def fav():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    userId = session['_user_id']
    products = db.execute_list(f"SELECT ad.id, ad.name, ad.price, ad.image FROM ad, fav WHERE ad.id = fav.productId AND fav.userId = {userId}")
    return render_template("fav.html", products=products, title='Избранное')


@app.route("/removeFromFav")
def removeFromFav():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        db.insert(f"DELETE FROM fav WHERE userid = {userId} AND productid = {productId}")
        flash("Товар удален из корзины")
    except:
        flash("Ошибка", 'error')
    return redirect(url_for('fav'))


@app.route('/newProduct', methods=["POST", "GET"])
def new_product():
    product = {'name': '', 'price': '', 'description': '', 'category': '', 'quantity': ''}
    if request.method == "POST":
        file = request.files['photo']
        filename = secure_filename(file.filename)
        if filename != '':
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        category = request.form['category']
        quantity = request.form['quantity']
        if len(name) > 3 and int(price) >= 0 and len(description) > 4:
            db.insert(f"INSERT INTO ad (id, name, price, description, quantity, category, image) VALUES(default, '{name}', {price}, '{description}', {quantity}, '{category}', '{filename}')")
            flash("Товар добавлен")
            return redirect(url_for('products'))
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("new_product.html", title="Новый продукт", product=product)


@app.route("/removeProduct")
def removeProduct():
    productId = int(request.args.get('productId'))
    db.insert(f"DELETE FROM fav WHERE productid = {productId}")
    db.insert(f"DELETE FROM kart WHERE productid = {productId}")
    db.insert(f"DELETE FROM ad WHERE id = {productId}")
    flash("Товар удален")
    return redirect(url_for('products'))


@app.route("/redirectProduct", methods=["POST", "GET"])
def redirectProduct():
    if request.args.get('productId') is not None:
        session['product_id'] = request.args.get('productId')
    product = db.execute(f"select id, name, price, description, category, quantity from ad where id={session['product_id']}")
    if request.method == "POST":
        file = request.files['photo']
        filename = secure_filename(file.filename)
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        category = request.form['category']
        quantity = request.form['quantity']
        if len(name) > 4 and len(description) > 4:
            if filename == '':
                db.insert(f"UPDATE ad SET name='{name}', price={price}, description='{description}', category='{category}', quantity={quantity} WHERE id = '{session['product_id']}'")
            else:
                db.insert(
                    f"UPDATE ad SET name='{name}', price={price}, description='{description}', category='{category}', quantity={quantity}, image='{filename}' WHERE id = '{session['product_id']}'")
            flash("Товар изменен")
            return redirect(url_for('products'))
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("new_product.html", title="Редактировать товар", product=product, url=url_for('redirectProduct'))


@app.route("/makeOrder")
def makeOrder():
    if session['products'] != []:
        db.insert(f"INSERT INTO orders (userid, productid) VALUES({session['_user_id']}, '{set(session['products'])}')")
        db.insert(f"DELETE FROM kart WHERE userid = {session['_user_id']}")
        session['products'] = []
        flash("Закан сделан")
    else:
        flash("Пустой заказ", 'error')
    return redirect(url_for('cart'))


@app.route('/profile')
@login_required
def profile():
    orders = db.execute_list(f"select productid from orders where userid={session['_user_id']}")
    orders_list = []
    for row in orders:
        orders_list.append(row['productid'])
    orders = []
    for row in orders_list:
        p1 = []
        for elem in row:
            res = db.execute(f"select * from ad where id={elem}")
            p1.append(res)
        orders.append(p1)
    prof = db.execute(f"select * from users where id={session['_user_id']}")
    return render_template("profile.html", title="Профиль", orders=orders, prof=prof)


@app.route("/redirectProfile", methods=["POST", "GET"])
def redirectProfile():
    prof = db.execute(f"select * from users where id={session['_user_id']}")
    if request.method == "POST":
        emails = db.execute(f"SELECT email FROM users")
        list_emails = []
        for email in emails:
            list_emails.append(email['email'])
        if len(request.form['email']) > 4 and request.form['psw'] == request.form['psw2'] and (request.form['email'] not in list_emails or request.form['email'] == session['user_name']):
            if request.form['psw'] == '':
                db.insert(f"UPDATE users SET email='{request.form['email']}' WHERE id = {session['_user_id']}")
            else:
                hash = generate_password_hash(request.form['psw'])
                db.insert(f"UPDATE users SET email='{request.form['email']}', password='{hash}' WHERE id = '{session['_user_id']}'")
            flash("Профиль изменен")
            return redirect(url_for('profile'))
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("registration.html", title="Редактировать профиль", prof=prof)


@app.route("/removeProfile")
def removeProfile():
    userId = session['_user_id']
    logout_user()
    db.insert(f"DELETE FROM fav WHERE userid = {userId}")
    db.insert(f"DELETE FROM kart WHERE userid = {userId}")
    db.insert(f"DELETE FROM orders WHERE userid = {userId}")
    db.insert(f"DELETE FROM users WHERE id = {userId}")
    flash("Товар удален")
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)