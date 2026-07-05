from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime

from utils.jsondb import load_users, save_users, load_orders, save_orders
from utils.chatbot import get_bot_response
from utils.recommendation import recommend_foods
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "smartcanteen_secret_key"

socketio = SocketIO(app, async_mode='eventlet')

from flask_socketio import join_room

@socketio.on('connect')
def handle_connect():
    if session.get("admin"):
        join_room("admin_dashboard")
    elif session.get("user_id"):
        join_room(f'user_{session["user_id"]}')

# ================= FOOD =================
def load_foods():
    with open("data/foods.json", "r") as f:
        return json.load(f)


def save_foods(data):
    with open("data/foods.json", "w") as f:
        json.dump(data, f, indent=4)


# ================= HOME =================
@app.route("/")
def index():
    return render_template("index.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        users = load_users()

        for u in users:
            if u["email"] == request.form["email"]:
                flash("Email already exists")
                return redirect("/register")

        users.append({
            "id": len(users) + 1,
            "name": request.form["name"],
            "email": request.form["email"],
            "password": generate_password_hash(request.form["password"]),
            "role": "user"
        })

        save_users(users)
        return redirect("/login")

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        users = load_users()
        print("Users loaded:", users)
        print("Total users:", len(users))

        email = request.form["email"].strip()
        password = request.form["password"]

        print("Login Email:", email)

        for u in users:
            print("Checking:", u)

            if u["email"].strip().lower() == email.lower():

                print("Email Matched")

                if check_password_hash(u["password"], password):

                    print("Password Matched")

                    session["user"] = u["name"]
                    session["user_id"] = u["id"]
                    session["cart"] = []

                    return redirect("/home")
                else:
                    print("Password Wrong")

        flash("Invalid credentials")

    return render_template("login.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= HOME =================
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/login")

    return render_template("home.html", user=session["user"])


# ================= MENU =================
@app.route("/menu")
def menu():
    if "user" not in session:
        return redirect("/login")

    foods = load_foods()
    return render_template("menu.html", foods=foods)


# ================= ADD TO CART =================
@app.route("/add_to_cart/<int:food_id>")
def add_to_cart(food_id):

    foods = load_foods()
    item = next((f for f in foods if f["id"] == food_id), None)

    if not item:
        return redirect("/menu")

    cart = session.get("cart", [])

    for c in cart:
        if c["id"] == food_id:
            c["quantity"] += 1
            session["cart"] = cart
            return redirect("/cart")

    cart.append({
        "id": item["id"],
        "name": item["name"],
        "price": item["price"],
        "image": item["image"],
        "quantity": 1
    })

    session["cart"] = cart
    return redirect("/cart")


# ================= CART =================
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/login")

    cart = session.get("cart", [])
    total = sum(i["price"] * i["quantity"] for i in cart)

    return render_template("cart.html", cart=cart, total=total)


# ================= UPDATE CART =================
@app.route("/update_cart/<int:food_id>/<action>")
def update_cart(food_id, action):

    cart = session.get("cart", [])

    for item in cart:
        if item["id"] == food_id:

            if action == "increase":
                item["quantity"] += 1
            elif action == "decrease":
                item["quantity"] -= 1

            if item["quantity"] <= 0:
                cart.remove(item)

            break

    session["cart"] = cart
    session.modified = True

    return redirect("/cart")


# ================= REMOVE ITEM =================
@app.route("/remove_item/<int:food_id>")
def remove_item(food_id):

    cart = session.get("cart", [])
    cart = [i for i in cart if i["id"] != food_id]

    session["cart"] = cart
    session.modified = True

    return redirect("/cart")


# ================= PLACE ORDER (FIXED) =================
@app.route("/place_order", methods=["POST"])
def place_order():

    if "user" not in session:
        return redirect("/login")

    cart = session.get("cart", [])

    if not cart:
        return redirect("/cart")

    orders = load_orders()

    total = sum(item["price"] * item["quantity"] for item in cart)

    coupon = request.form.get("coupon", "").strip().upper().replace("","")

    discount = 0

    if coupon == "SAVE10":
       discount = total * 0.10

    final_total = total - discount

    payment_method = request.form.get("payment_method", "Cash on Delivery")
    payment_status = request.form.get("payment_status", "Paid")
    payment_id = "PAY" + datetime.now().strftime("%Y%m%d%H%M%S")

    orders.append({
    "id": len(orders) + 1,
    "customer": session["user"],
    "user_id": session["user_id"],
    "items": cart,
    "total": final_total,
    "discount": discount,
    "coupon": coupon,
    "status":"Placed",
    "payment_status": payment_status,
    "payment_method": payment_method,
    "payment_id": payment_id,
    "rating": 0,
    "date": datetime.now().strftime("%d-%m-%Y %H:%M")
})

    save_orders(orders)
    
    socketio.emit('new_notification', {
       'message': f"New order #{orders[-1]['id']} received",
       'type': 'new_order'
    },   room='admin_dashboard')


    session["cart"] = []

    return redirect("/orders")


# ================= ORDERS =================
@app.route("/orders")
def orders():

    if "user" not in session:
        return redirect("/login")

    all_orders = load_orders()

    my_orders = [o for o in all_orders if o["customer"] == session["user"]]

    return render_template("orders.html", orders=my_orders)


# ================= CHATBOT =================
@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():

    if "user" not in session:
        return redirect("/login")

    response = ""

    if request.method == "POST":
        message = request.form["message"]
        response = get_bot_response(message)

    return render_template("chatbot.html", response=response)


# ================= ADMIN LOGIN =================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        admin = json.load(open("data/admin.json"))

        if request.form["email"] == admin["email"] and request.form["password"] == admin["password"]:
            session["admin"] = True
            return redirect("/admin/dashboard")

        flash("Invalid admin login")

    return render_template("admin_login.html")


# ================= ADMIN DASHBOARD =================
@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin/login")

    orders = load_orders()
    users = load_users()
    foods = load_foods()

    total_sales = sum(o["total"] for o in orders)
    avg_order = total_sales / len(orders) if orders else 0

    return render_template(
        "admin_dashboard.html",
        orders=orders,
        users=len(users),
        foods=len(foods),
        sales=total_sales,
        avg_order=avg_order
    )


# ================= UPDATE ORDER =================
@app.route("/admin/update_order/<int:id>/<status>")
def update_order(id, status):

    if "admin" not in session:
        return redirect("/admin/login")

    orders = load_orders()

    for o in orders:
        if o["id"] == id:
            o["status"] = status

    save_orders(orders)
    return redirect("/admin/dashboard")

@app.route("/admin/add_food", methods=["GET", "POST"])
def admin_add_food():

    if "admin" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        foods = load_foods()

        new_food = {
            "id": len(foods) + 1,
            "name": request.form["name"],
            "price": float(request.form["price"]),
            "category": request.form["category"],
            "image": request.form["image"],
            "rating": 4.5
        }

        foods.append(new_food)
        save_foods(foods)

        flash("Food Added Successfully!")
        return redirect("/admin/dashboard")

    return render_template("add_food.html")


@app.route("/recommend", methods=["GET", "POST"])
def recommend():

    if "user" not in session:
        return redirect("/login")

    foods = load_foods()
    recommended = []

    if request.method == "POST":

        preference = request.form.get("preference", "").lower()
        max_price = request.form.get("max_price")

        for food in foods:

            tags = [tag.lower() for tag in food.get("tags", [])]

            # Match preference using tags
            if preference not in tags:
                continue

            # Budget filter
            if max_price:
                if float(food["price"]) > float(max_price):
                    continue

            recommended.append(food)

    return render_template(
        "recommend.html",
        foods=recommended
    )

@app.route("/payment")
def payment():

    if "user" not in session:
        return redirect("/login")

    cart = session.get("cart", [])

    if not cart:
        return redirect("/cart")

    total = sum(item["price"] * item["quantity"] for item in cart)

    return render_template("payment.html", total=total)


# ================= ORDER RATING =================
@app.route("/rate/<int:order_id>/<int:rating>")
def rate_order(order_id, rating):

    if "user" not in session:
        return redirect("/login")

    orders = load_orders()

    for order in orders:
        if order["id"] == order_id:
            order["rating"] = rating
            break

    save_orders(orders)

    flash("⭐ Rating Submitted Successfully!")

    return redirect("/orders")  

@app.route("/invoice/<int:id>")
def invoice(id):

    if "user" not in session:
        return redirect("/login")

    orders = load_orders()

    order = next((o for o in orders if o["id"] == id), None)
 
    print(order)

    if order is None:
        return "Invoice not found"

    return render_template("invoice.html", order=order)

@app.route('/admin/order_ready/<int:order_id>')
def order_ready(order_id):

    orders = load_orders()

    found = False

    for order in orders:
        if order["id"] == order_id:

            order["status"] = "Ready"

            socketio.emit('new_notification', {
                  'message': f"Order #{order['id']} is now Ready",
                  'type': 'order_status'
                }, room=f"user_{order['user_id']}")

            found = True
            break

    if found:
        save_orders(orders)
        return redirect("/admin/dashboard")
    else:
        return "Order not found"


@app.route("/order_ready_page")
def order_ready_page():
    return render_template("order_ready.html")    

@app.route("/test")
def test():
    return "OK"

# ================= RUN =================
if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)