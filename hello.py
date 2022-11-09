import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from db_util import Database
from UserLogin import UserLogin

app = Flask(__name__)

app.secret_key = "111"
app.permanent_session_lifetime = datetime.timedelta(days=365)

db = Database()

login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, db)


@app.route('/', methods=['GET', 'POST'])
def products():
    category = request.form.get('category')
    #category = request.args.get("category")
    if category:
        products = db.execute(f"SELECT * FROM ad WHERE category='{category}'")
    else:
        products = db.execute(f"SELECT * FROM ad")
    context = {
        'products': products,
        'title': "PRODUCTS",
        'category': category,
    }
    return render_template("products.html", **context)


@app.route("/product/<int:product_id>")
def get_product(product_id):
    try:
        product = db.execute(f"select id, name, price, description, category from ad where id='{product_id}'")
        if db.execute_list(f"SELECT * FROM fav WHERE productid = {product_id} and userid = {session['_user_id']}") == []:
            in_fav = False
        else:
            in_fav = True
        return render_template("product.html", title=product['name'], product=product, in_fav=in_fav)
    except:
        return render_template("error.html", error="Такого фильма не существует в системе")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        emails = db.execute(f"SELECT email FROM users")
        list_emails = []
        for email in emails:
            list_emails.append(email['email'])
        if len(request.form['email']) > 4 and len(request.form['psw']) > 4 and request.form['psw'] == request.form['psw2'] and request.form['email'] not in list_emails:
            hash = generate_password_hash(request.form['psw'])
            db.insert(f"INSERT INTO users values (default, '{request.form['email']}', '{hash}');")
            flash("Вы успешно зарегистрированы")
            return redirect(url_for('login'))
        else:
            flash("Неверно заполнены поля", "error")
    return render_template("registration.html", title="Регистрация")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user = db.getUserByEmail(request.form['email'])
        if user and check_password_hash(user[2], request.form['psw']):
            userlogin = UserLogin().create(user)
            login_user(userlogin)
            return redirect(url_for('products'))
        flash("Неверный логин или пароль", "error")
    return render_template("login.html", title="Авторизация")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html", title="Профиль")
#f"""<p><a href="{url_for('logout')}">Выйти</a><p>user info: {current_user.get_id()}"""


@app.route("/addToCart")
def addToCart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        db.insert(f"INSERT INTO kart (userId, productId) VALUES ({userId}, {productId})")
        msg = "Added successfully"
    except:
        msg = "Error occured"
    return redirect(url_for('products'))


@app.route("/cart")
def cart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    userId = session['_user_id']
    products = db.execute_list(f"SELECT ad.id, ad.name, ad.price FROM ad, kart WHERE ad.id = kart.productId AND kart.userId = {userId}")
    totalPrice = 0
    for row in products:
        totalPrice += row['price']
    return render_template("cart.html", products = products, totalPrice=totalPrice)


@app.route("/removeFromCart")
def removeFromCart():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        db.insert(f"DELETE FROM kart WHERE userId = {userId} AND productId = {productId}")
        msg = "removed successfully"
    except:
        msg = "Error occured"
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
            msg = "Added successfully"
        else:
            msg = "Error occured"
    except:
        msg = "Error occured"
    return redirect(url_for('products'))


@app.route("/fav")
def fav():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    userId = session['_user_id']
    products = db.execute_list(f"SELECT ad.id, ad.name, ad.price FROM ad, fav WHERE ad.id = fav.productId AND fav.userId = {userId}")
    return render_template("fav.html", products=products)


@app.route("/removeFromFav")
def removeFromFav():
    if '_user_id' not in session:
        return redirect(url_for('login'))
    productId = int(request.args.get('productId'))
    userId = session['_user_id']
    try:
        db.insert(f"DELETE FROM fav WHERE userId = {userId} AND productId = {productId}")
        msg = "removed successfully"
    except:
        msg = "Error occured"
    return redirect(url_for('fav'))


@app.route('/newProduct', methods=["POST", "GET"])
def new_product():
    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        category = request.form['category']
        quantity = request.form['quantity']
        if len(name) > 4 and int(price) >= 0 and len(description) > 4:
            db.insert(f"INSERT INTO ad (id, name, price, description, quantity, category) VALUES(default, '{name}', {price}, '{description}', {quantity}, '{category}')")
            return redirect(url_for('products'))
    return render_template("new_product.html", title="Новый фильм")


@app.route("/removeProduct")
def removeProduct():
    productId = int(request.args.get('productId'))
    db.insert(f"DELETE FROM fav WHERE productid = {productId}")
    db.insert(f"DELETE FROM kart WHERE productid = {productId}")
    db.insert(f"DELETE FROM ad WHERE id = {productId}")
    return redirect(url_for('products'))


if __name__ == "__main__":
    app.run(debug=True)