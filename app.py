import sqlite3
from flask import Flask, render_template, request, redirect, session
from datetime import date, datetime, timedelta

app = Flask(__name__)
app.secret_key = "secret123"

def init_db():
    conn = sqlite3.connect("habits.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        streak INTEGER DEFAULT 0,
        last_done TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/test")
def test():
    return "TEST ROUTE WORKING"

@app.route("/signup", methods=["GET", "POST"])
def signup():
    print("Rendering signup.html now")
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not email or not password or not confirm:
            return render_template("signup.html", error="All fields required")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        if not email.endswith("@gmail.com"):
            return render_template("signup.html", error="Enter a valid Gmail")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            db.commit()
            return redirect("/login")
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Account already exists")


    return render_template("signup.html")

def get_db():
    conn = sqlite3.connect("habits.db")
    conn.row_factory = sqlite3.Row  # allow dict-like access
    return conn


@app.route("/")
def index():
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    habits = db.execute("SELECT * FROM habits").fetchall()
    return render_template("index.html", habits=habits)
@app.route("/delete/<int:id>")
def delete(id):
    db = get_db()
    db.execute("DELETE FROM habits WHERE id=?", (id,))
    db.commit()
    return redirect("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        if user:
            session["user"] = user[1]  # store the email in session
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/done/<int:habit_id>")
def done(habit_id):
    db = get_db()
    habit = db.execute(
        "SELECT last_done, streak FROM habits WHERE id=?",
        (habit_id,)
    ).fetchone()

    last_done_str = habit["last_done"] if isinstance(habit, dict) or hasattr(habit, '__getitem__') else habit[0]
    if last_done_str:
        last_done = datetime.strptime(last_done_str, "%Y-%m-%d").date()
    else:
        last_done = None

    today = date.today()

    if last_done == today:
        return redirect("/")  # already marked today

    if last_done is None:
        streak = 1
    else:
        streak = habit["streak"] + 1 if (today - last_done).days == 1 else 1

    db.execute(
        "UPDATE habits SET streak=?, last_done=? WHERE id=?",
        (streak, today.strftime("%Y-%m-%d"), habit_id)
    )
    db.commit()

    return redirect("/")
@app.route("/add", methods=["GET", "POST"])
def add_habit():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("add.html", error="Enter a habit name")

        db = get_db()
        db.execute(
            "INSERT INTO habits (name, streak, last_done) VALUES (?, 0, '')",
            (name,)
        )
        db.commit()
        return redirect("/")

    return render_template("add.html")

if __name__ == "__main__":
    app.run(debug=True)
