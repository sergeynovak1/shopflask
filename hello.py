import datetime
from flask import Flask, render_template, request

from db_util import Database

app = Flask(__name__)

app.secret_key = "111"
app.permanent_session_lifetime = datetime.timedelta(days=365)
db = Database()


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
        product = db.execute(f"select * from ad where id='{product_id}'")
        return render_template("product.html", title=product['name'], product=product)
    except:
        return render_template("error.html", error="Такого фильма не существует в системе")



if __name__ == "__main__":
    app.run(debug=True)