
import os
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ------------ Image Upload Setup ------------
ALLOWED_EXT = {"jpg", "jpeg", "png"}

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

UPLOAD_FOLDER = "static/products"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ------------ Database Setup ------------
def connect_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    return conn

# ------------ Routes ------------

@app.route("/")
def index():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = connect_db()
        try:
            conn.execute("INSERT INTO users(username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return render_template("register.html", error="Username already exists!")

        conn.close()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect_db()
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session["username"] = username
            return redirect("/home")
        else:
            return render_template("login.html", error="Invalid username or password!")

    return render_template("login.html")

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/login")
    return render_template("home.html", username=session["username"])


# ------------ PROJECT: Upload + Detect + Compare Prices ------------
@app.route("/project", methods=["GET", "POST"])
def project():
    if "username" not in session:
        return redirect("/login")

    uploaded = None
    product = None
    error = None

    if request.method == "POST":
        if "photo" not in request.files:
            error = "No file selected."
            return render_template("project.html", error=error)

        photo = request.files["photo"]

        if photo.filename == "":
            error = "Please choose an image."
            return render_template("project.html", error=error)

        if not allowed(photo.filename):
            error = "Only JPG, JPEG, PNG allowed!"
            return render_template("project.html", error=error)

        # Save file correctly
        filename = secure_filename(photo.filename).lower().replace(" ", "_")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        photo.save(save_path)

        # Correct path for the browser
        uploaded = f"/static/products/{filename}"

        fname = filename.lower()

        # -------- Dummy Product Detection --------
        if "laptop" in fname:
            product = {"name": "Laptop", "amazon": "₹55,000", "flipkart": "₹53,499", "walmart": "$620"}
        elif "phone" in fname:
            product = {"name": "Smartphone", "amazon": "₹29,000", "flipkart": "₹27,999", "walmart": "$330"}
        elif "camera" in fname:
            product = {"name": "Camera", "amazon": "₹42,999", "flipkart": "₹41,999", "walmart": "$510"}
        elif "watch" in fname:
            product = {"name": "Smartwatch", "amazon": "₹3,499", "flipkart": "₹3,299", "walmart": "$45"}
        else:
            product = {"name": "Unknown Product", "amazon": "-", "flipkart": "-", "walmart": "-"}

    return render_template("project.html", uploaded=uploaded, product=product, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
