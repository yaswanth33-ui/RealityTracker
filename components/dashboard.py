import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

def render_dashboard(db):
    st.title("Financial Dashboard")

    # Summary Cards
    summary = db.get_summary()
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
        monthly = transactions.set_index('date').resample('M').agg({
            'amount': lambda x: pd.Series(x[transactions.loc[x.index, 'type'] == 'Income']).sum(),
            'type': 'first'
        }).fillna(0)

        monthly_expenses = transactions[transactions['type'] == 'Expense'].set_index('date').resample('M')['amount'].sum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly['amount'],
            name='Income',
            line=dict(color='#2E7D32', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=monthly_expenses.index,
            y=monthly_expenses,
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
        expenses = transactions[transactions['type'] == 'Expense']

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
                fig = px.pie(
                    filtered_expenses,
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
            all_tags = [tag for tags in filtered_expenses['tags'] for tag in tags]
            if all_tags:
                tag_counts = pd.Series(all_tags).value_counts()
                st.write("Most used tags:", ", ".join(tag_counts.head().index))

        else:
            st.info("No expense data available for the selected period")
    else:
        st.info("Add some transactions to see your financial overview!")