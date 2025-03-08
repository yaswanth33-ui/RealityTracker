import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def calculate_financial_health_score(income, expenses, savings, budget_adherence):
    """Calculate financial health score based on various metrics"""
    score = 0
    
    # Income to expense ratio (30 points)
    if income > 0:
        expense_ratio = expenses / income
        if expense_ratio <= 0.5: score += 30
        elif expense_ratio <= 0.7: score += 20
        elif expense_ratio <= 0.9: score += 10
    
    # Savings rate (30 points)
    if income > 0:
        savings_rate = savings / income
        if savings_rate >= 0.2: score += 30
        elif savings_rate >= 0.1: score += 20
        elif savings_rate > 0: score += 10
    
    # Budget adherence (40 points)
    if budget_adherence >= 90: score += 40
    elif budget_adherence >= 80: score += 30
    elif budget_adherence >= 70: score += 20
    elif budget_adherence >= 60: score += 10
    
    return score

import pandas as pd
from datetime import datetime, timedelta
from components.notifications import check_budget_alerts, render_alerts, check_financial_goal_alerts

def render_dashboard(db):
    st.title("Financial Dashboard")

    # Check and display alerts
    budget_alerts = check_budget_alerts(db)
    goal_alerts = check_financial_goal_alerts(db)

    # Get notification settings
    settings = db.get_notification_settings()
    threshold = 80
    if not settings.empty:
        threshold = settings.iloc[0]['budget_alert_threshold']

    # Filter alerts based on threshold
    filtered_budget_alerts = [alert for alert in budget_alerts if alert['percentage'] >= threshold]

    # Render alerts
    if filtered_budget_alerts or goal_alerts:
        st.subheader("Notifications")
        with st.expander("View Alerts", expanded=True):
            render_alerts(filtered_budget_alerts)
            render_alerts(goal_alerts)

    # Get summary data
    summary = db.get_summary()
    
    # Calculate financial health metrics
    income = summary['total_income']
    expenses = summary['total_expenses']
    savings = income - expenses
    
    # Calculate budget adherence
    budget_goals = db.get_budget_goals()
    budget_adherence = 100
    if not budget_goals.empty:
        adherence_scores = []
        for _, goal in budget_goals.iterrows():
            actual = summary['categories'].get(goal['category'], 0)
            if goal['amount'] > 0:
                adherence = (1 - abs(actual - goal['amount']) / goal['amount']) * 100
                adherence_scores.append(max(0, min(100, adherence)))
        if adherence_scores:
            budget_adherence = sum(adherence_scores) / len(adherence_scores)
    
    # Calculate health score
    health_score = calculate_financial_health_score(income, expenses, savings, budget_adherence)
    
    # Display health score
    st.subheader("Financial Health Score")
    score_col1, score_col2 = st.columns([1, 3])
    with score_col1:
        st.markdown(f"""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #4CAF50, #2196F3); border-radius: 10px;'>
                <h1 style='color: white; margin: 0;'>{health_score}</h1>
                <p style='color: white; margin: 0;'>/ 100</p>
            </div>
        """, unsafe_allow_html=True)
    with score_col2:
        st.markdown("### Score Breakdown")
        st.markdown(f"- Income to Expense Ratio: {'Healthy' if expenses/income <= 0.7 else 'Needs Attention'}")
        st.markdown(f"- Savings Rate: {(savings/income*100):.1f}%")
        st.markdown(f"- Budget Adherence: {budget_adherence:.1f}%")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Income", 
            f"${summary['total_income']:,.2f}",
            help="Total income from all sources"
        )
    with col2:
        st.metric(
            "Total Expenses", 
            f"${summary['total_expenses']:,.2f}",
            help="Total expenses across all categories"
        )
    with col3:
        net_worth = summary['net_worth']
        st.metric(
            "Net Worth", 
            f"${net_worth:,.2f}",
            delta=f"${net_worth:,.2f}",
            delta_color="normal" if net_worth >= 0 else "inverse",
            help="Total income minus total expenses"
        )

    # Transaction Overview
    transactions = db.get_transactions()
    if not transactions.empty:
        # Monthly Trend
        st.subheader("Monthly Income vs Expenses")
        transactions['date'] = pd.to_datetime(transactions['date'])

        # Calculate monthly trends separately for income and expenses
        income_monthly = transactions[transactions['type'] == 'Income'].copy()
        expense_monthly = transactions[transactions['type'] == 'Expense'].copy()

        income_trend = income_monthly.groupby(income_monthly['date'].dt.strftime('%Y-%m'))['amount'].sum()
        expense_trend = expense_monthly.groupby(expense_monthly['date'].dt.strftime('%Y-%m'))['amount'].sum()

        # Combine all dates for complete timeline
        all_dates = pd.Series(index=sorted(set(income_trend.index) | set(expense_trend.index))).fillna(0)
        income_trend = income_trend.reindex(all_dates.index, fill_value=0)
        expense_trend = expense_trend.reindex(all_dates.index, fill_value=0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=income_trend.index,
            y=income_trend.values,
            name='Income',
            line=dict(color='#2E7D32', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=expense_trend.index,
            y=expense_trend.values,
            name='Expenses',
            line=dict(color='#1976D2', width=2)
        ))
        fig.update_layout(
            title='Monthly Income vs Expenses Trend',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            template='plotly_white',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Category Distribution
        st.subheader("Expense Distribution")
        expenses = transactions[transactions['type'] == 'Expense'].copy()

        # Time period selection for expenses
        period = st.select_slider(
            "Select Time Period",
            options=['Last Month', 'Last 3 Months', 'Last 6 Months', 'Year to Date', 'All Time'],
            value='Last Month'
        )

        end_date = datetime.now()
        if period == 'Last Month':
            start_date = end_date - timedelta(days=30)
        elif period == 'Last 3 Months':
            start_date = end_date - timedelta(days=90)
        elif period == 'Last 6 Months':
            start_date = end_date - timedelta(days=180)
        elif period == 'Year to Date':
            start_date = datetime(end_date.year, 1, 1)
        else:
            start_date = expenses['date'].min()

        filtered_expenses = expenses[
            (expenses['date'] >= start_date) & 
            (expenses['date'] <= end_date)
        ]

        if not filtered_expenses.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart for categories
                category_data = filtered_expenses.groupby('category')['amount'].sum().reset_index()
                fig = px.pie(
                    category_data,
                    values='amount',
                    names='category',
                    title='Expense Distribution by Category',
                    color_discrete_sequence=px.colors.sequential.Greens
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Bar chart for top spending categories
                category_expenses = filtered_expenses.groupby('category')['amount'].sum().sort_values(ascending=True)
                fig = px.bar(
                    category_expenses,
                    orientation='h',
                    title='Top Spending Categories',
                    color_discrete_sequence=['#1976D2']
                )
                fig.update_layout(
                    xaxis_title='Amount ($)',
                    yaxis_title='Category',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

            # Transaction tags word cloud
            st.subheader("Popular Transaction Tags")
            all_tags = [tag for tags in filtered_expenses['tags'] for tag in tags if tags]
            if all_tags:
                tag_counts = pd.Series(all_tags).value_counts()
                st.write("Most used tags:", ", ".join(tag_counts.head().index))

            # Summary statistics
            st.subheader("Summary Statistics")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            with stats_col1:
                avg_expense = filtered_expenses['amount'].mean()
                st.metric("Average Expense", f"${avg_expense:.2f}")
            with stats_col2:
                total_expense = filtered_expenses['amount'].sum()
                st.metric("Total Expenses", f"${total_expense:.2f}")
            with stats_col3:
                transaction_count = len(filtered_expenses)
                st.metric("Number of Transactions", transaction_count)

        else:
            st.info("No expense data available for the selected period")
    else:
        st.info("Add some transactions to see your financial overview!")