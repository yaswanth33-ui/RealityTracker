import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

def render_reports(db):
    st.title("Financial Reports")
    
    transactions = db.get_transactions()
    if not transactions.empty:
        transactions['date'] = pd.to_datetime(transactions['date'])
        
        # Time Period Selection
        period = st.selectbox(
            "Select Time Period",
            ["Last 30 Days", "Last 3 Months", "Last 6 Months", "Year to Date", "All Time"]
        )
        
        # Filter data based on selected period
        end_date = datetime.now()
        if period == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif period == "Last 3 Months":
            start_date = end_date - timedelta(days=90)
        elif period == "Last 6 Months":
            start_date = end_date - timedelta(days=180)
        elif period == "Year to Date":
            start_date = datetime(end_date.year, 1, 1)
        else:
            start_date = transactions['date'].min()
            
        filtered_data = transactions[
            (transactions['date'] >= start_date) &
            (transactions['date'] <= end_date)
        ]
        
        # Spending Patterns
        st.subheader("Spending Patterns")
        expenses = filtered_data[filtered_data['type'] == 'Expense']
        
        if not expenses.empty:
            # Daily spending trend
            daily_expenses = expenses.groupby('date')['amount'].sum().reset_index()
            fig = px.line(
                daily_expenses,
                x='date',
                y='amount',
                title='Daily Spending Trend',
                line_shape='spline'
            )
            fig.update_traces(line_color='#2E7D32')
            st.plotly_chart(fig, use_container_width=True)
            
            # Category breakdown
            category_expenses = expenses.groupby('category')['amount'].sum().reset_index()
            fig = px.bar(
                category_expenses,
                x='category',
                y='amount',
                title='Expenses by Category',
                color_discrete_sequence=['#1976D2']
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Daily Spending", 
                         f"${daily_expenses['amount'].mean():.2f}")
            with col2:
                st.metric("Highest Spending Day", 
                         f"${daily_expenses['amount'].max():.2f}")
            with col3:
                st.metric("Most Expensive Category", 
                         f"{category_expenses.iloc[category_expenses['amount'].argmax()]['category']}")
        else:
            st.info("No expense data available for the selected period.")
    else:
        st.info("Add some transactions to generate financial reports!")
