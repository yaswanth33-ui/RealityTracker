import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_dashboard(db):
    st.title("Financial Dashboard")
    
    # Summary Cards
    summary = db.get_summary()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Income", f"${summary['total_income']:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${summary['total_expenses']:,.2f}")
    with col3:
        st.metric("Net Worth", f"${summary['net_worth']:,.2f}")

    # Transaction Overview
    transactions = db.get_transactions()
    if not transactions.empty:
        # Monthly Trend
        transactions['date'] = pd.to_datetime(transactions['date'])
        monthly = transactions.set_index('date').resample('M').sum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly[transactions['type'] == 'Income']['amount'],
            name='Income',
            line=dict(color='#2E7D32')
        ))
        fig.add_trace(go.Scatter(
            x=monthly.index,
            y=monthly[transactions['type'] == 'Expense']['amount'],
            name='Expenses',
            line=dict(color='#1976D2')
        ))
        fig.update_layout(
            title='Monthly Income vs Expenses',
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Category Distribution
        expenses = transactions[transactions['type'] == 'Expense']
        if not expenses.empty:
            fig = px.pie(
                expenses,
                values='amount',
                names='category',
                title='Expense Distribution by Category',
                color_discrete_sequence=px.colors.sequential.Greens
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add some transactions to see your financial overview!")
