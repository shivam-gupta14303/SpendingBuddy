import sqlite3

# =========================
# DATABASE CONNECTION
# =========================

conn = sqlite3.connect("spendingbuddy.db")
cursor = conn.cursor()


# =========================
# USERS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    source TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# =========================
# EXPENSES TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    expense_type TEXT NOT NULL,
    priority TEXT NOT NULL,
    note TEXT,
    date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# =========================
# BILLS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bill_name TEXT NOT NULL,
    amount REAL NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# =========================
# BUDGET TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    monthly_limit REAL NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# =========================
# SETTINGS TABLE
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    income REAL DEFAULT 0,
    budget_limit REAL DEFAULT 5000,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")


# =========================
# SAVE CHANGES
# =========================

conn.commit()
conn.close()

print("Database and tables created successfully!")