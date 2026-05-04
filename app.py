from collections import defaultdict
from datetime import datetime
import os
import sqlite3

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.config["SECRET_KEY"] = "replace-this-with-a-random-secret-key"
app.config["DATABASE"] = os.path.join(BASE_DIR, "expense_tracker.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    )
    db.commit()


@app.before_request
def ensure_database():
    init_db()


def is_logged_in():
    return "user_id" in session


def validate_expense_form(name, amount, date_value):
    if not name or not amount or not date_value:
        return "All expense fields are required."

    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return "Amount must be greater than 0."
    except ValueError:
        return "Amount must be a valid number."

    try:
        datetime.strptime(date_value, "%Y-%m-%d")
    except ValueError:
        return "Date must be valid and in YYYY-MM-DD format."

    return None


@app.route("/", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("login"))

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            flash("Login successful", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid login credentials", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if is_logged_in():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing_user:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hashed_password),
        )
        db.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    expenses = db.execute(
        """
        SELECT id, name, amount, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        """,
        (session["user_id"],),
    ).fetchall()

    return render_template("dashboard.html", expenses=expenses, user_email=session.get("email"))


@app.route("/add", methods=["POST"])
def add_expense():
    if not is_logged_in():
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    amount = request.form.get("amount", "").strip()
    date_value = request.form.get("date", "").strip()

    error_message = validate_expense_form(name, amount, date_value)
    if error_message:
        flash(error_message, "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO expenses (user_id, name, amount, date) VALUES (?, ?, ?, ?)",
        (session["user_id"], name, float(amount), date_value),
    )
    db.commit()
    flash("Expense added successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/edit/<int:expense_id>", methods=["POST"])
def edit_expense(expense_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    amount = request.form.get("amount", "").strip()
    date_value = request.form.get("date", "").strip()

    error_message = validate_expense_form(name, amount, date_value)
    if error_message:
        flash(error_message, "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    expense = db.execute(
        "SELECT id FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    ).fetchone()
    if not expense:
        flash("Expense not found or access denied.", "error")
        return redirect(url_for("dashboard"))

    db.execute(
        "UPDATE expenses SET name = ?, amount = ?, date = ? WHERE id = ? AND user_id = ?",
        (name, float(amount), date_value, expense_id, session["user_id"]),
    )
    db.commit()
    flash("Expense updated successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    result = db.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"]),
    )
    db.commit()

    if result.rowcount == 0:
        flash("Expense not found or access denied.", "error")
    else:
        flash("Expense deleted successfully.", "success")

    return redirect(url_for("dashboard"))


@app.route("/report")
def report():
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    expenses = db.execute(
        """
        SELECT name, amount, date
        FROM expenses
        WHERE user_id = ?
        ORDER BY date ASC, id ASC
        """,
        (session["user_id"],),
    ).fetchall()

    total_expenses = sum(expense["amount"] for expense in expenses)
    number_of_expenses = len(expenses)
    average_expense = total_expenses / number_of_expenses if number_of_expenses else 0
    highest_expense = max((expense["amount"] for expense in expenses), default=0)

    grouped_by_date = defaultdict(float)
    for expense in expenses:
        grouped_by_date[expense["date"]] += expense["amount"]

    chart_labels = list(grouped_by_date.keys())
    chart_values = [round(grouped_by_date[date_key], 2) for date_key in chart_labels]

    return render_template(
        "report.html",
        total_expenses=round(total_expenses, 2),
        number_of_expenses=number_of_expenses,
        average_expense=round(average_expense, 2),
        highest_expense=round(highest_expense, 2),
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
