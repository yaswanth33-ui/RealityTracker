import streamlit as st
import pandas as pd
from database import Database
from components.dashboard import render_dashboard
from components.transactions import render_transactions
from components.budget import render_budget
from components.reports import render_reports

# Page configuration
st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return Database()

db = get_database()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Transactions", "Budget", "Reports"]
)

# Main content
if page == "Dashboard":
    render_dashboard(db)
elif page == "Transactions":
    render_transactions(db)
elif page == "Budget":
    render_budget(db)
else:
    render_reports(db)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Your Finance Manager")
