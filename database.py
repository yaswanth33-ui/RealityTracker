import sqlite3
import pandas as pd
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('finance.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )''')

        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS budget_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL
        )''')
        
        self.conn.commit()

    def add_transaction(self, date, type, category, amount, description):
        self.conn.execute(
            'INSERT INTO transactions (date, type, category, amount, description) VALUES (?, ?, ?, ?, ?)',
            (date, type, category, amount, description)
        )
        self.conn.commit()

    def get_transactions(self):
        return pd.read_sql_query('SELECT * FROM transactions', self.conn)

    def set_budget_goal(self, category, amount, period):
        self.conn.execute(
            'INSERT OR REPLACE INTO budget_goals (category, amount, period) VALUES (?, ?, ?)',
            (category, amount, period)
        )
        self.conn.commit()

    def get_budget_goals(self):
        return pd.read_sql_query('SELECT * FROM budget_goals', self.conn)

    def get_summary(self):
        df = self.get_transactions()
        if df.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'net_worth': 0
            }
        
        total_income = df[df['type'] == 'Income']['amount'].sum()
        total_expenses = df[df['type'] == 'Expense']['amount'].sum()
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_worth': total_income - total_expenses
        }
