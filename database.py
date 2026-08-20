import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# =========================
# DATABASE CONNECTION
# =========================

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()


# =========================
# USERS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT,
    google_id TEXT UNIQUE
)
""")


# =========================
# INCOME TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS income (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount REAL NOT NULL,
    source TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL
)
""")


# =========================
# EXPENSES TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    expense_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


# =========================
# BILLS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS bills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    bill_name TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending'
)
""")


# =========================
# BUDGET TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT NOT NULL,
    monthly_limit REAL NOT NULL
)
""")


# =========================
# SETTINGS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    income REAL DEFAULT 0,
    budget_limit REAL DEFAULT 5000
)
""")


# =========================
# SAVE CHANGES
# =========================

conn.commit()
conn.close()

print("PostgreSQL database and tables created successfully!")