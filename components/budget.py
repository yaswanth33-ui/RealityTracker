import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from components.notifications import check_budget_alerts, render_alerts, check_financial_goal_alerts

def validate_budget_goal(amount, category, existing_goals):
    if amount <= 0:
        st.error("Budget amount must be greater than zero")
        return False
    if category in existing_goals['category'].values:
        st.warning(f"Budget goal for {category} already exists. The existing goal will be updated.")
    return True

def validate_financial_goal(name, amount, target_date):
    if not name.strip():
        st.error("Goal name cannot be empty")
        return False
    if amount <= 0:
        st.error("Target amount must be greater than zero")
        return False
    if target_date <= datetime.now().date():
        st.error("Target date must be in the future")
        return False
    return True

def render_budget(db):
    st.title("Budget Planning")
    
    # Display budget alerts
    budget_alerts = check_budget_alerts(db)
    if budget_alerts:
        st.subheader("Budget Alerts")
        render_alerts(budget_alerts)
    
    # Display financial goal alerts
    goal_alerts = check_financial_goal_alerts(db)
    if goal_alerts:
        st.subheader("Financial Goal Alerts")
        render_alerts(goal_alerts)

    tab1, tab2 = st.tabs(["Budget Goals", "Financial Goals"])

    with tab1:
        # Budget Goal Setting
        with st.form("budget_form"):
            col1, col2 = st.columns(2)

            with col1:
                category = st.selectbox(
                    "Category",
                    ["Food", "Transport", "Housing", "Utilities", "Entertainment", "Shopping", "Healthcare", "Other"]
                )

            with col2:
                amount = st.number_input("Monthly Budget Amount", min_value=0.01, format="%.2f")

            if st.form_submit_button("Set Budget"):
                budget_goals = db.get_budget_goals()
                if validate_budget_goal(amount, category, budget_goals):
                    try:
                        db.set_budget_goal(category, amount, 'monthly')
                        st.success("Budget goal set successfully!")
                    except Exception as e:
                        st.error(f"Error setting budget goal: {str(e)}")

        # Budget vs Actual
        st.subheader("Budget vs Actual Spending")

        budget_goals = db.get_budget_goals()
        transactions = db.get_transactions()

        if not budget_goals.empty and not transactions.empty:
            current_month = datetime.now().strftime("%Y-%m")
            monthly_expenses = transactions[
                (transactions['type'] == 'Expense') &
                (transactions['date'].dt.strftime("%Y-%m") == current_month)
            ].groupby('category')['amount'].sum()

            comparison_data = []
            for _, row in budget_goals.iterrows():
                actual = monthly_expenses.get(row['category'], 0)
                remaining = max(row['amount'] - actual, 0)
                percentage = (actual / row['amount'] * 100) if row['amount'] > 0 else 0

                comparison_data.append({
                    'category': row['category'],
                    'Budget': row['amount'],
                    'Actual': actual,
                    'Remaining': remaining,
                    'Percentage': percentage
                })

            if comparison_data:
                df_comparison = pd.DataFrame(comparison_data)

                # Progress bars
                for idx, row in df_comparison.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        progress = row['Percentage'] / 100
                        color = 'red' if progress > 1 else 'normal'
                        st.progress(min(progress, 1.0))
                    with col2:
                        st.write(f"{row['category']}: ${row['Actual']:,.2f} / ${row['Budget']:,.2f}")
                        if progress > 1:
                            st.warning("⚠️ Over budget!")

                # Detailed comparison chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Budget',
                    x=df_comparison['category'],
                    y=df_comparison['Budget'],
                    marker_color='#2E7D32'
                ))
                fig.add_trace(go.Bar(
                    name='Actual',
                    x=df_comparison['category'],
                    y=df_comparison['Actual'],
                    marker_color='#1976D2'
                ))
                fig.update_layout(
                    barmode='group',
                    title='Budget vs Actual Spending by Category',
                    template='plotly_white'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Download budget report
                if st.button("Export Budget Report"):
                    report = df_comparison.to_csv(index=False)
                    st.download_button(
                        label="Download Report",
                        data=report,
                        file_name=f"budget_report_{current_month}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("Set budget goals and add transactions to see your budget analysis!")

    with tab2:
        st.subheader("Financial Goals")

        # Goal Setting Form
        with st.form("financial_goal_form"):
            goal_name = st.text_input("Goal Name", placeholder="e.g., Emergency Fund, New Car")
            goal_amount = st.number_input("Target Amount", min_value=0.01, format="%.2f")
            goal_date = st.date_input("Target Date", min_value=datetime.now().date())

            if st.form_submit_button("Add Financial Goal"):
                if validate_financial_goal(goal_name, goal_amount, goal_date):
                    try:
                        db.add_financial_goal(goal_name, goal_amount, goal_date.strftime("%Y-%m-%d"))
                        st.success("Financial goal added successfully!")
                    except Exception as e:
                        st.error(f"Error adding financial goal: {str(e)}")

        # Display Financial Goals
        financial_goals = db.get_financial_goals()
        if not financial_goals.empty:
            st.subheader("Your Goals")
            for _, goal in financial_goals.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    progress = (goal['current_amount'] / goal['target_amount']) * 100
                    st.write(f"### {goal['name']}")
                    st.progress(progress / 100)
                    st.write(f"${goal['current_amount']:,.2f} of ${goal['target_amount']:,.2f} ({progress:.1f}%)")
                with col2:
                    days_left = (pd.to_datetime(goal['target_date']) - pd.Timestamp.now()).days
                    st.write(f"Days left: {max(days_left, 0)}")
                    if days_left < 0:
                        st.warning("Goal overdue!")
                st.markdown("---")
        else:
            st.info("Add your first financial goal to start tracking!")