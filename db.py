"""Capa de datos: SQLite local, un solo archivo (finanzas.db)."""

import os
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = os.environ.get("FINANZAS_DB", str(Path(__file__).parent / "finanzas.db"))


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id   INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS incomes (
                id     INTEGER PRIMARY KEY,
                date   TEXT NOT NULL,
                amount INTEGER NOT NULL,
                note   TEXT
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY,
                name        TEXT NOT NULL,
                category_id INTEGER REFERENCES categories(id),
                amount      INTEGER NOT NULL,
                date        TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS purchases (
                id                INTEGER PRIMARY KEY,
                merchant          TEXT NOT NULL,
                category_id       INTEGER REFERENCES categories(id),
                total_amount      INTEGER NOT NULL,
                installments      INTEGER NOT NULL DEFAULT 1,
                installment_value INTEGER NOT NULL,
                date              TEXT NOT NULL
            );
            """
        )


# --- Categorías ---------------------------------------------------------


def get_or_create_category(name):
    name = name.strip()
    if not name:
        return None
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        row = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (name,)
        ).fetchone()
        return row["id"]


def list_categories():
    with get_conn() as conn:
        return [
            r["name"]
            for r in conn.execute("SELECT name FROM categories ORDER BY name")
        ]


def category_usage():
    """Categorías con cuántos gastos y compras usan cada una."""
    with get_conn() as conn:
        return pd.read_sql_query(
            """
            SELECT c.id, c.name AS categoria,
                   (SELECT COUNT(*) FROM expenses e WHERE e.category_id = c.id) AS gastos,
                   (SELECT COUNT(*) FROM purchases p WHERE p.category_id = c.id) AS compras
            FROM categories c
            ORDER BY c.name
            """,
            conn,
        )


def delete_category(cat_id):
    """Elimina una categoría solo si no está en uso. Devuelve True si se borró."""
    with get_conn() as conn:
        used = conn.execute(
            """
            SELECT (SELECT COUNT(*) FROM expenses WHERE category_id = ?)
                 + (SELECT COUNT(*) FROM purchases WHERE category_id = ?)
            """,
            (cat_id, cat_id),
        ).fetchone()[0]
        if used:
            return False
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
        return True


# --- Ingresos ------------------------------------------------------------


def add_income(date, amount, note=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO incomes (date, amount, note) VALUES (?, ?, ?)",
            (date.isoformat(), amount, note.strip()),
        )


def incomes_df():
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT id, date, amount, note FROM incomes ORDER BY date DESC, id DESC",
            conn,
        )


def delete_income(income_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM incomes WHERE id = ?", (income_id,))


# --- Gastos ---------------------------------------------------------------


def add_expense(name, category_name, amount, date):
    cat_id = get_or_create_category(category_name)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO expenses (name, category_id, amount, date) VALUES (?, ?, ?, ?)",
            (name.strip(), cat_id, amount, date.isoformat()),
        )


def expense_names():
    with get_conn() as conn:
        return [
            r["name"]
            for r in conn.execute(
                "SELECT DISTINCT name FROM expenses ORDER BY name COLLATE NOCASE"
            )
        ]


def expenses_df():
    with get_conn() as conn:
        return pd.read_sql_query(
            """
            SELECT e.id, e.name, COALESCE(c.name, '(sin categoría)') AS categoria,
                   e.amount, e.date
            FROM expenses e LEFT JOIN categories c ON c.id = e.category_id
            ORDER BY e.date DESC, e.id DESC
            """,
            conn,
        )


def delete_expense(expense_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


# --- Compras (con o sin cuotas) -------------------------------------------


def add_purchase(merchant, category_name, total, installments, installment_value, date):
    cat_id = get_or_create_category(category_name)
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO purchases
                (merchant, category_id, total_amount, installments, installment_value, date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (merchant.strip(), cat_id, total, installments, installment_value, date.isoformat()),
        )


def merchant_names():
    with get_conn() as conn:
        return [
            r["merchant"]
            for r in conn.execute(
                "SELECT DISTINCT merchant FROM purchases ORDER BY merchant COLLATE NOCASE"
            )
        ]


def purchases_df():
    with get_conn() as conn:
        return pd.read_sql_query(
            """
            SELECT p.id, p.merchant, COALESCE(c.name, '(sin categoría)') AS categoria,
                   p.total_amount, p.installments, p.installment_value, p.date
            FROM purchases p LEFT JOIN categories c ON c.id = p.category_id
            ORDER BY p.date DESC, p.id DESC
            """,
            conn,
        )


def delete_purchase(purchase_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
