import os
from flask import Flask, render_template, request, redirect, session, url_for
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))


# =========================================================
# HOME / DASHBOARD
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Make sure this user has a settings row
    # -----------------------------------------------------
    cursor.execute("SELECT id FROM settings WHERE user_id = %s", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO settings (user_id, income, budget_limit) VALUES (%s, 0, 5000)",
            (user_id,)
        )
        conn.commit()

    # -----------------------------------------------------
    # Handle income being saved from the dashboard form
    # -----------------------------------------------------
    if request.method == "POST":
        new_income = request.form["income"]
        cursor.execute(
            "UPDATE settings SET income = %s WHERE user_id = %s",
            (new_income, user_id)
        )
        conn.commit()

    # -----------------------------------------------------
    # Read income + budget limit
    # -----------------------------------------------------
    cursor.execute("SELECT income, budget_limit FROM settings WHERE user_id = %s", (user_id,))
    income, budget_limit = cursor.fetchone()

    # -----------------------------------------------------
    # TOTAL EXPENSES
    # -----------------------------------------------------
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s", (user_id,))
    total_expenses = cursor.fetchone()[0] or 0

    current_balance = income - total_expenses

    # -----------------------------------------------------
    # RECENT EXPENSES
    # -----------------------------------------------------
    cursor.execute("""
        SELECT amount, category, note, date
        FROM expenses
        WHERE user_id = %s
        ORDER BY date DESC, id DESC
        LIMIT 5
    """, (user_id,))
    rows = cursor.fetchall()
    recent_expenses = [
        {"title": note if note else category, "amount": -amount, "date": date, "category": category}
        for amount, category, note, date in rows
    ]

    # -----------------------------------------------------
    # CATEGORY BREAKDOWN
    # -----------------------------------------------------
    cursor.execute("""
        SELECT category, SUM(amount) FROM expenses
        WHERE user_id = %s GROUP BY category ORDER BY SUM(amount) DESC
    """, (user_id,))
    categories = [{"name": category, "amount": amount} for category, amount in cursor.fetchall()]

    # -----------------------------------------------------
    # BILLS
    # -----------------------------------------------------
    cursor.execute("SELECT SUM(amount) FROM bills WHERE user_id = %s AND status = 'Paid'", (user_id,))
    paid_bills = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM bills WHERE user_id = %s AND status = 'Pending'", (user_id,))
    upcoming_bills = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT SUM(amount) FROM bills
        WHERE user_id = %s AND status = 'Pending'
        AND (due_date::date - CURRENT_DATE) BETWEEN 0 AND 3
    """, (user_id,))
    due_soon = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT COUNT(*) FROM bills
        WHERE user_id = %s AND status = 'Pending'
        AND (CURRENT_DATE - due_date::date) > 0
    """, (user_id,))
    overdue_count = cursor.fetchone()[0] or 0

    conn.close()

    return render_template(
        "home.html",
        current_balance=current_balance,
        income=income,
        expenses=total_expenses,
        recent_expenses=recent_expenses,
        categories=categories,
        budget_limit=budget_limit,
        paid_bills=paid_bills,
        upcoming_bills=upcoming_bills,
        due_soon=due_soon,
        overdue_count=overdue_count
    )


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        expense_type = request.form["expense_type"]
        priority = request.form["priority"]
        note = request.form["note"]
        date = request.form["date"]

        user_id = session["user_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO expenses
            (
                user_id,
                amount,
                category,
                expense_type,
                priority,
                note,
                date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            amount,
            category,
            expense_type,
            priority,
            note,
            date
        ))

        conn.commit()
        conn.close()

        return render_template(
            "add_expense.html",
            success=True
        )

    return render_template(
        "add_expense.html",
        success=False
    )


# =========================================================
# VIEW EXPENSES
# =========================================================

@app.route("/expenses")
def view_expenses():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            amount,
            category,
            expense_type,
            priority,
            note,
            date
        FROM expenses
        WHERE user_id = %s
        ORDER BY date DESC, id DESC
    """, (user_id,))

    expenses = cursor.fetchall()


    # Total spent by current user

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = %s
    """, (user_id,))

    total_spent = cursor.fetchone()[0] or 0

    conn.close()


    return render_template(
        "expenses.html",
        expenses=expenses,
        total_spent=total_spent
    )


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route("/delete-expense/<int:expense_id>")
def delete_expense(expense_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM expenses
        WHERE id = %s
        AND user_id = %s
    """, (expense_id, user_id))

    conn.commit()
    conn.close()

    return redirect("/expenses")


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports", methods=["GET", "POST"])
def reports():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # TODAY'S SPENDING
    # -----------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = %s
        AND date = TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD')
    """, (user_id,))

    today_spent = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # THIS MONTH'S SPENDING
    # -----------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = %s
        AND TO_CHAR(date::date, 'YYYY-MM')
            = TO_CHAR(CURRENT_DATE, 'YYYY-MM')
    """, (user_id,))

    month_spent = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # TOTAL SPENDING
    # -----------------------------------------------------

    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = %s
    """, (user_id,))

    total_spent = cursor.fetchone()[0] or 0


    # -----------------------------------------------------
    # CATEGORY-WISE SPENDING
    # -----------------------------------------------------

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = %s
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (user_id,))

    category_data = cursor.fetchall()


    # -----------------------------------------------------
    # CUSTOM DATE RANGE
    # -----------------------------------------------------

    range_total = None
    start_date = ""
    end_date = ""


    if request.method == "POST":

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        cursor.execute("""
            SELECT SUM(amount)
            FROM expenses
            WHERE user_id = %s
            AND date BETWEEN %s AND %s
        """, (user_id, start_date, end_date))

        range_total = cursor.fetchone()[0] or 0


    conn.close()


    return render_template(
        "reports.html",
        today_spent=today_spent,
        month_spent=month_spent,
        total_spent=total_spent,
        category_data=category_data,
        range_total=range_total,
        start_date=start_date,
        end_date=end_date
    )


# =========================================================
# ADD BILL
# =========================================================

@app.route("/add-bill", methods=["GET", "POST"])
def add_bill():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        bill_name = request.form["bill_name"]
        amount = request.form["amount"]
        due_date = request.form["due_date"]

        user_id = session["user_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO bills
            (
                user_id,
                bill_name,
                amount,
                due_date
            )
            VALUES (%s, %s, %s, %s)
        """, (
            user_id,
            bill_name,
            amount,
            due_date
        ))

        conn.commit()
        conn.close()

        return {"success": True}


    return render_template("add_bill.html")


# =========================================================
# VIEW BILLS
# =========================================================

@app.route("/bills")
def view_bills():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # ALL BILLS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            bill_name,
            amount,
            due_date,
            status
        FROM bills
        WHERE user_id = %s
        ORDER BY due_date
    """, (user_id,))

    bills = cursor.fetchall()


    # -----------------------------------------------------
    # BILLS DUE WITHIN 3 DAYS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            bill_name,
            amount,
            due_date,
            status
        FROM bills
        WHERE user_id = %s
        AND status = 'Pending'
        AND (due_date::date - CURRENT_DATE)
            BETWEEN 0 AND 3
        ORDER BY due_date
    """, (user_id,))

    urgent_bills = cursor.fetchall()


    conn.close()


    return render_template(
        "bills.html",
        bills=bills,
        urgent_bills=urgent_bills
    )


# =========================================================
# MARK BILL AS PAID
# =========================================================

@app.route("/mark-paid/<int:bill_id>")
def mark_paid(bill_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()


    # -----------------------------------------------------
    # Get bill only if it belongs to current user
    # -----------------------------------------------------

    cursor.execute("""
        SELECT bill_name, amount
        FROM bills
        WHERE id = %s
        AND user_id = %s
        AND status = 'Pending'
    """, (bill_id, user_id))

    bill = cursor.fetchone()


    if bill is None:
        conn.close()
        return redirect("/bills")


    bill_name, amount = bill


    # -----------------------------------------------------
    # Mark bill as paid
    # -----------------------------------------------------

    cursor.execute("""
        UPDATE bills
        SET status = 'Paid'
        WHERE id = %s
        AND user_id = %s
    """, (bill_id, user_id))


    # -----------------------------------------------------
    # Add bill payment to expenses
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO expenses
        (
            user_id,
            amount,
            category,
            expense_type,
            priority,
            note,
            date
        )
        VALUES (%s, %s, %s, %s, %s, %s, TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD'))
    """, (
        user_id,
        amount,
        "Bills",
        "Bill Payment",
        "Medium",
        bill_name
    ))


    conn.commit()
    conn.close()

    return redirect("/bills")


# =========================================================
# DELETE BILL
# =========================================================

@app.route("/delete-bill/<int:bill_id>")
def delete_bill(bill_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM bills
        WHERE id = %s
        AND user_id = %s
    """, (bill_id, user_id))

    conn.commit()
    conn.close()

    return redirect("/bills")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"]
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES (%s, %s, %s)
            """, (
                username,
                email,
                password
            ))

            conn.commit()
            conn.close()

            return redirect("/login")


        except psycopg2.IntegrityError:

            conn.rollback()
            conn.close()

            return "Username or Email already exists"


    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                username,
                password
            FROM users
            WHERE username = %s
        """, (username,))

        user = cursor.fetchone()

        conn.close()


        if user and user[2] and check_password_hash(
            user[2],
            password
        ):

            session["user_id"] = user[0]
            session["username"] = user[1]

            return redirect("/")

        else:

            return "Invalid username or password"


    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# ACCOUNT
# =========================================================

@app.route("/account")
def account():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("account.html")

@app.route("/login/google")
def login_google():
    redirect_uri = url_for('login_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# ===========================================================
# Google Login
# ===========================================================

@app.route("/login/google/callback")
def login_google_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE google_id = %s", (google_id,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (username, email, google_id) VALUES (%s, %s, %s) RETURNING id",
            (name, email, google_id)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        username = name
    else:
        user_id, username = user

    conn.close()

    session["user_id"] = user_id
    session["username"] = username

    return redirect("/")

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(debug=True)