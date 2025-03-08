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
            tags TEXT DEFAULT '[]',
            recurring_id INTEGER,
            FOREIGN KEY (recurring_id) REFERENCES recurring_transactions(id)
        )''')

        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS recurring_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            frequency TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            last_generated TEXT,
            tags TEXT DEFAULT '[]',
            active BOOLEAN DEFAULT 1
        )''')

        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            icon TEXT,
            color TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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

    def add_recurring_transaction(self, name, type, category, amount, description, frequency, start_date, end_date=None, tags=None):
        tags_json = json.dumps(tags or [])
        self.conn.execute(
            '''INSERT INTO recurring_transactions 
               (name, type, category, amount, description, frequency, start_date, end_date, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, type, category, amount, description, frequency, start_date, end_date, tags_json)
        )
        self.conn.commit()

    def get_recurring_transactions(self):
        df = pd.read_sql_query('SELECT * FROM recurring_transactions WHERE active = 1', self.conn)
        if not df.empty:
            df['tags'] = df['tags'].apply(lambda x: json.loads(x) if x else [])
        return df

    def add_custom_category(self, name, type, icon=None, color=None):
        try:
            self.conn.execute(
                'INSERT INTO custom_categories (name, type, icon, color) VALUES (?, ?, ?, ?)',
                (name, type, icon, color)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_custom_categories(self):
        return pd.read_sql_query('SELECT * FROM custom_categories', self.conn)

    def get_all_categories(self):
        custom_categories = self.get_custom_categories()
        default_categories = pd.DataFrame({
            'name': ["Salary", "Investment", "Food", "Transport", "Housing", "Utilities", 
                    "Entertainment", "Shopping", "Healthcare", "Other"],
            'type': ['Income', 'Income', 'Expense', 'Expense', 'Expense', 'Expense',
                    'Expense', 'Expense', 'Expense', 'Expense']
        })
        return pd.concat([custom_categories[['name', 'type']], default_categories])

    def get_transactions(self):
        df = pd.read_sql_query('SELECT * FROM transactions', self.conn)
        if not df.empty:
            # Convert tags from JSON string to list
            df['tags'] = df['tags'].apply(lambda x: json.loads(x) if x else [])
            # Ensure date is in datetime format
            df['date'] = pd.to_datetime(df['date'])
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
                'categories': {},
                'monthly_trends': {}
            }

        total_income = df[df['type'] == 'Income']['amount'].sum()
        total_expenses = df[df['type'] == 'Expense']['amount'].sum()

        # Calculate expense categories
        categories = df[df['type'] == 'Expense'].groupby('category')['amount'].sum().to_dict()

        # Calculate monthly trends
        monthly_data = {}
        for type_ in ['Income', 'Expense']:
            type_data = df[df['type'] == type_].copy()
            if not type_data.empty:
                monthly = type_data.groupby(type_data['date'].dt.strftime('%Y-%m'))['amount'].sum()
                monthly_data[type_] = monthly.to_dict()
            else:
                monthly_data[type_] = {}

        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_worth': total_income - total_expenses,
            'categories': categories,
            'monthly_trends': monthly_data
        }