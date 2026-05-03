"""
WealthFlow Database — SQLite (dev) or PostgreSQL (production)
"""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Try PostgreSQL, fall back to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_POSTGRES = DATABASE_URL.startswith("postgres")

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor


def get_connection():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        DB_PATH = Path(__file__).parent / "wealthflow.db"
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def _execute(cursor, sql: str, params=()):
    """Execute SQL, translating ? placeholders to %s for PostgreSQL."""
    if USE_POSTGRES:
        sql = sql.replace("?", "%s")
    cursor.execute(sql, params)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Investments
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS investments (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            invested REAL NOT NULL,
            current_value REAL NOT NULL,
            date TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else
        """
        CREATE TABLE IF NOT EXISTS investments (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            invested REAL NOT NULL,
            current_value REAL NOT NULL,
            date TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Expenses
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT DEFAULT 'upi',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT DEFAULT 'upi',
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Budgets
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category)
        )
        """ if USE_POSTGRES else
        """
        CREATE TABLE IF NOT EXISTS budgets (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            limit_amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category)
        )
        """
    )

    # Recurring
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recurring_expenses (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            frequency TEXT NOT NULL DEFAULT 'monthly',
            day_of_month INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            last_paid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """ if USE_POSTGRES else
        """
        CREATE TABLE IF NOT EXISTS recurring_expenses (
            id REAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            frequency TEXT NOT NULL DEFAULT 'monthly',
            day_of_month INTEGER DEFAULT 1,
            active INTEGER DEFAULT 1,
            last_paid TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()

    # ---- SQLite migrations only ----
    if not USE_POSTGRES:
        _migrate_sqlite(cursor, conn)

    conn.close()


def _migrate_sqlite(cursor, conn):
    """Add missing columns to existing SQLite DB."""
    def add_col(table, col, col_type):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if col not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            conn.commit()

    add_col("expenses", "payment_method", "TEXT DEFAULT 'upi'")
    add_col("investments", "user_id", "INTEGER DEFAULT 0")
    add_col("expenses", "user_id", "INTEGER DEFAULT 0")
    add_col("budgets", "user_id", "INTEGER DEFAULT 0")
    add_col("recurring_expenses", "user_id", "INTEGER DEFAULT 0")


def _fetchall(cursor) -> List[dict]:
    if USE_POSTGRES:
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    else:
        return [dict(row) for row in cursor.fetchall()]


def _fetchone(cursor) -> Optional[dict]:
    rows = _fetchall(cursor)
    return rows[0] if rows else None


# ---- User Auth ----

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT * FROM users WHERE email = %s", (email,))
    row = _fetchone(cursor)
    conn.close()
    return row


def create_user(email, password_hash, name):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "INSERT INTO users (email, password_hash, name) VALUES (%s, %s, %s) RETURNING id" if USE_POSTGRES else "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)", (email, password_hash, name))
    if USE_POSTGRES:
        user_id = cursor.fetchone()[0]
    else:
        user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": user_id, "email": email, "name": name}


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT id, email, name, created_at FROM users WHERE id = %s", (user_id,))
    row = _fetchone(cursor)
    conn.close()
    return row


# ---- Investments ----

def get_investments(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT * FROM investments WHERE user_id = %s ORDER BY date DESC", (user_id,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def add_investment(inv):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor,
        "INSERT OR REPLACE INTO investments (id, user_id, name, type, invested, current_value, date, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)" if not USE_POSTGRES else
        "INSERT INTO investments (id, user_id, name, type, invested, current_value, date, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET user_id=EXCLUDED.user_id, name=EXCLUDED.name, type=EXCLUDED.type, invested=EXCLUDED.invested, current_value=EXCLUDED.current_value, date=EXCLUDED.date, note=EXCLUDED.note",
        (inv["id"], inv["user_id"], inv["name"], inv["type"], inv["invested"], inv["current_value"], inv["date"], inv.get("note", "")))
    conn.commit()
    conn.close()
    return inv


def delete_investment(inv_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "DELETE FROM investments WHERE id = %s AND user_id = %s", (inv_id, user_id))
    conn.commit()
    conn.close()


def update_investment_current_value(inv_id, user_id, current_value):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "UPDATE investments SET current_value = %s WHERE id = %s AND user_id = %s", (current_value, inv_id, user_id))
    conn.commit()
    conn.close()


# ---- Expenses ----

def get_expenses(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC", (user_id,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def add_expense(exp):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor,
        "INSERT OR REPLACE INTO expenses (id, user_id, description, amount, date, category, payment_method, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)" if not USE_POSTGRES else
        "INSERT INTO expenses (id, user_id, description, amount, date, category, payment_method, note) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET user_id=EXCLUDED.user_id, description=EXCLUDED.description, amount=EXCLUDED.amount, date=EXCLUDED.date, category=EXCLUDED.category, payment_method=EXCLUDED.payment_method, note=EXCLUDED.note",
        (exp["id"], exp["user_id"], exp["description"], exp["amount"], exp["date"], exp["category"], exp.get("payment_method", "upi"), exp.get("note", "")))
    conn.commit()
    conn.close()
    return exp


def delete_expense(exp_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "DELETE FROM expenses WHERE id = %s AND user_id = %s", (exp_id, user_id))
    conn.commit()
    conn.close()


# ---- Recurring ----

def get_recurring_expenses(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT * FROM recurring_expenses WHERE user_id = %s AND active = 1 ORDER BY day_of_month", (user_id,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def add_recurring_expense(rec):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor,
        "INSERT OR REPLACE INTO recurring_expenses (id, user_id, name, amount, category, frequency, day_of_month, active, last_paid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" if not USE_POSTGRES else
        "INSERT INTO recurring_expenses (id, user_id, name, amount, category, frequency, day_of_month, active, last_paid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET user_id=EXCLUDED.user_id, name=EXCLUDED.name, amount=EXCLUDED.amount, category=EXCLUDED.category, frequency=EXCLUDED.frequency, day_of_month=EXCLUDED.day_of_month, active=EXCLUDED.active, last_paid=EXCLUDED.last_paid",
        (rec["id"], rec["user_id"], rec["name"], rec["amount"], rec["category"], rec.get("frequency", "monthly"), rec.get("day_of_month", 1), rec.get("active", 1), rec.get("last_paid", "")))
    conn.commit()
    conn.close()
    return rec


def delete_recurring_expense(rec_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "DELETE FROM recurring_expenses WHERE id = %s AND user_id = %s", (rec_id, user_id))
    conn.commit()
    conn.close()


def update_recurring_last_paid(rec_id, user_id, last_paid):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "UPDATE recurring_expenses SET last_paid = %s WHERE id = %s AND user_id = %s", (last_paid, rec_id, user_id))
    conn.commit()
    conn.close()


# ---- Budgets ----

def get_budgets(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT * FROM budgets WHERE user_id = %s", (user_id,))
    rows = _fetchall(cursor)
    conn.close()
    return rows


def add_budget(budget):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor,
        "INSERT OR REPLACE INTO budgets (id, user_id, category, limit_amount) VALUES (%s, %s, %s, %s)" if not USE_POSTGRES else
        "INSERT INTO budgets (id, user_id, category, limit_amount) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, category) DO UPDATE SET limit_amount=EXCLUDED.limit_amount",
        (budget["id"], budget["user_id"], budget["category"], budget["limit"]))
    conn.commit()
    conn.close()
    return budget


def delete_budget(budget_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "DELETE FROM budgets WHERE id = %s AND user_id = %s", (budget_id, user_id))
    conn.commit()
    conn.close()
