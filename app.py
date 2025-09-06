from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, datetime, difflib

app = Flask(__name__)
app.secret_key = "supersecret123"   

def init_db():
    conn = sqlite3.connect("ecofinds.db")
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        email TEXT UNIQUE,
                        password TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        title TEXT,
                        category TEXT,
                        description TEXT,
                        price REAL,
                        created_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

def suggest_category(title):
    keywords = {
        "Clothing": ["shirt", "jeans", "tshirt", "dress", "jacket"],
        "Electronics": ["phone", "laptop", "camera", "tablet"],
        "Books": ["book", "novel", "magazine"],
        "Furniture": ["chair", "table", "sofa", "bed"],
        "Other": []
    }
    title_lower = title.lower()
    for cat, words in keywords.items():
        for word in words:
            if word in title_lower:
                return cat
    return "Other"

@app.route("/")
def home():
    search = request.args.get("q")
    conn = sqlite3.connect("ecofinds.db")
    cur = conn.cursor()
    if search:
        cur.execute("SELECT * FROM products")
        all_products = cur.fetchall()
        products = [p for p in all_products if difflib.get_close_matches(search.lower(), [p[2].lower()], cutoff=0.5)]
    else:
        cur.execute("SELECT * FROM products ORDER BY datetime(created_at) DESC")
        products = cur.fetchall()
    conn.close()
    return render_template("home.html", products=products, search=search)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]  # stored as plain text ❌ (no hashing)

        conn = sqlite3.connect("ecofinds.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password) VALUES (?,?,?)",
                        (username, email, password))
            conn.commit()
        except:
            return "⚠️ Email already exists."
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("ecofinds.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid email or password"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("ecofinds.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE user_id=? ORDER BY datetime(created_at) DESC", (session["user_id"],))
    my_products = cur.fetchall()
    conn.close()
    return render_template("dashboard.html", products=my_products, username=session["username"])

@app.route("/add", methods=["GET", "POST"])
def add_product():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        price = request.form["price"]
        category = request.form["category"] or suggest_category(title)

        conn = sqlite3.connect("ecofinds.db")
        cur = conn.cursor()
        cur.execute("INSERT INTO products (user_id, title, category, description, price, created_at) VALUES (?,?,?,?,?,?)",
                    (session["user_id"], title, category, description, price, datetime.datetime.now()))
        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))
    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)

