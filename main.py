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
    ["Dashboard", "Transactions", "Budget", "Reports", "Settings"]
)

# Main content
if page == "Dashboard":
    render_dashboard(db)
elif page == "Transactions":
    render_transactions(db)
elif page == "Budget":
    render_budget(db)
elif page == "Reports":
    render_reports(db)
else:
    # Settings page
    st.title("Settings")
    
    # Notification Settings
    st.header("Notification Settings")
    
    # Get current settings
    settings = db.get_notification_settings()
    
    if not settings.empty:
        settings = settings.iloc[0]
        
        with st.form("notification_settings"):
            st.subheader("Budget Alerts")
            budget_threshold = st.slider(
                "Alert threshold (% of budget)",
                min_value=50,
                max_value=100,
                value=int(settings['budget_alert_threshold']),
                step=5,
                help="You'll be notified when your spending reaches this percentage of your budget"
            )
            
            st.subheader("Goal Deadline Alerts")
            goal_days = st.number_input(
                "Days before deadline",
                min_value=1,
                max_value=30,
                value=int(settings['goal_deadline_alert_days']),
                help="You'll be notified when a goal deadline is this many days away"
            )
            
            st.subheader("Email Notifications")
            email_enabled = st.checkbox(
                "Enable email notifications",
                value=bool(settings['email_notifications']),
                help="Send alerts to your email (not implemented yet)"
            )
            
            email_address = st.text_input(
                "Email address",
                value=settings['email_address'] if settings['email_address'] else "",
                disabled=not email_enabled
            )
            
            if st.form_submit_button("Save Settings"):
                try:
                    db.update_notification_settings(
                        budget_threshold,
                        goal_days,
                        email_enabled,
                        email_address if email_enabled else None
                    )
                    st.success("Settings saved successfully!")
                except Exception as e:
                    st.error(f"Error saving settings: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Your Finance Manager")
