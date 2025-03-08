import sqlite3
import pandas as pd
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('finance.db', check_same_thread=False)
        self.migrate_database()

    def migrate_database(self):
        # Get existing columns
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]

        # Add tags column if it doesn't exist
        if 'tags' not in columns:
            self.conn.execute('ALTER TABLE transactions ADD COLUMN tags TEXT DEFAULT "[]"')

        # Create tables if they don't exist
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            tags TEXT DEFAULT '[]'
        )''')

        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS budget_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            period TEXT NOT NULL
        )''')

        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )''')

        self.conn.commit()

    def add_transaction(self, date, type, category, amount, description, tags=None):
        tags_json = json.dumps(tags or [])
        self.conn.execute(
            'INSERT INTO transactions (date, type, category, amount, description, tags) VALUES (?, ?, ?, ?, ?, ?)',
            (date, type, category, amount, description, tags_json)
        )
        self.conn.commit()

    def get_transactions(self):
        df = pd.read_sql_query('SELECT * FROM transactions', self.conn)
        if not df.empty:
            # Convert tags from JSON string to list
            df['tags'] = df['tags'].apply(lambda x: json.loads(x) if x else [])
        return df

    def set_budget_goal(self, category, amount, period):
        self.conn.execute(
            'INSERT OR REPLACE INTO budget_goals (category, amount, period) VALUES (?, ?, ?)',
            (category, amount, period)
        )
        self.conn.commit()

    def get_budget_goals(self):
        return pd.read_sql_query('SELECT * FROM budget_goals', self.conn)

    def add_financial_goal(self, name, target_amount, target_date):
        self.conn.execute(
            'INSERT INTO financial_goals (name, target_amount, target_date) VALUES (?, ?, ?)',
            (name, target_amount, target_date)
        )
        self.conn.commit()

    def update_financial_goal(self, goal_id, current_amount):
        self.conn.execute(
            'UPDATE financial_goals SET current_amount = ? WHERE id = ?',
            (current_amount, goal_id)
        )
        self.conn.commit()

    def get_financial_goals(self):
        return pd.read_sql_query('SELECT * FROM financial_goals', self.conn)

    def get_summary(self):
        df = self.get_transactions()
        if df.empty:
            return {
                'total_income': 0,
                'total_expenses': 0,
                'net_worth': 0,
                'categories': {}
            }

        total_income = df[df['type'] == 'Income']['amount'].sum()
        total_expenses = df[df['type'] == 'Expense']['amount'].sum()

        # Calculate expense categories
        categories = df[df['type'] == 'Expense'].groupby('category')['amount'].sum().to_dict()

        # Calculate monthly trends
        df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
        monthly_trends = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0).to_dict('index')

        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_worth': total_income - total_expenses,
            'categories': categories,
            'monthly_trends': monthly_trends
        }