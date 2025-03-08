
import streamlit as st
import numpy as np
from datetime import datetime, timedelta

def calculate_monthly_savings(target_amount, current_savings, months, interest_rate):
    """Calculate required monthly savings to reach goal"""
    r = interest_rate / 100 / 12  # Monthly interest rate
    if r == 0:
        return (target_amount - current_savings) / months
    pmt = np.pmt(r, months, -current_savings, target_amount, when='end')
    return pmt

def render_savings_calculator():
    st.title("Savings Goal Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_amount = st.number_input("Target Amount ($)", min_value=0.0, value=10000.0, step=100.0)
        current_savings = st.number_input("Current Savings ($)", min_value=0.0, value=0.0, step=100.0)
    
    with col2:
        years = st.number_input("Time Frame (Years)", min_value=0.1, value=1.0, step=0.5)
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=2.0, step=0.1)
    
    months = int(years * 12)
    monthly_savings = calculate_monthly_savings(target_amount, current_savings, months, interest_rate)
    
    st.markdown("---")
    
    # Results display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Required Monthly Savings", f"${monthly_savings:.2f}")
    with col2:
        total_contributions = monthly_savings * months
        st.metric("Total Contributions", f"${total_contributions:.2f}")
    with col3:
        interest_earned = target_amount - current_savings - total_contributions
        st.metric("Interest Earned", f"${interest_earned:.2f}")
    
    # Progress timeline
    st.subheader("Savings Growth Timeline")
    timeline = []
    balance = current_savings
    
    for month in range(months + 1):
        timeline.append({
            'Month': month,
            'Balance': balance
        })
        # Monthly interest and contribution
        interest = balance * (interest_rate / 100 / 12)
        balance += interest + monthly_savings
    
    import pandas as pd
    df = pd.DataFrame(timeline)
    
    # Plot the timeline
    import plotly.express as px
    fig = px.line(
        df,
        x='Month',
        y='Balance',
        title='Projected Savings Growth',
        labels={'Balance': 'Balance ($)', 'Month': 'Months'},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
