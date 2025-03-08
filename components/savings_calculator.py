
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def calculate_monthly_savings(target_amount, current_savings, months, interest_rate):
    """Calculate required monthly savings to reach goal"""
    if months <= 0:
        return 0
    r = interest_rate / 100 / 12  # Monthly interest rate
    if r == 0:
        return (target_amount - current_savings) / months
    try:
        pmt = np.pmt(r, months, -current_savings, target_amount, when='end')
        return float(pmt) if not np.isinf(pmt) else 0
    except:
        return 0

def render_savings_calculator():
    st.title("Savings Goal Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_amount = st.number_input("Target Amount ($)", min_value=0.0, value=10000.0, step=100.0)
        current_savings = st.number_input("Current Savings ($)", min_value=0.0, max_value=target_amount, value=0.0, step=100.0)
    
    with col2:
        years = st.number_input("Time Frame (Years)", min_value=0.1, max_value=50.0, value=1.0, step=0.5)
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=30.0, value=2.0, step=0.1)
    
    # Initialize variables
    monthly_savings = 0
    months = 0
    total_contributions = 0
    interest_earned = 0
    show_results = False

    if st.button("Calculate Savings Plan", type="primary"):
        months = int(years * 12)
        monthly_savings = calculate_monthly_savings(target_amount, current_savings, months, interest_rate)
        
        if monthly_savings <= 0:
            st.warning("Please check your input values. The calculation may not be possible with the current parameters.")
            return
            
        total_contributions = monthly_savings * months
        interest_earned = target_amount - current_savings - total_contributions
        show_results = True
        st.markdown("---")
    
        # Results display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Required Monthly Savings", f"${monthly_savings:.2f}")
        with col2:
            st.metric("Total Contributions", f"${total_contributions:.2f}")
        with col3:
            st.metric("Interest Earned", f"${interest_earned:.2f}")
    
    if show_results:
        # Progress timeline
        st.subheader("Savings Growth Timeline")
        
        try:
            timeline = []
            balance = current_savings
            
            for month in range(months + 1):
                if balance <= target_amount * 2:  # Prevent plotting beyond reasonable values
                    timeline.append({
                        'Month': month,
                        'Balance': round(balance, 2)
                    })
                    # Monthly interest and contribution
                    interest = balance * (interest_rate / 100 / 12)
                    balance = balance + interest + monthly_savings
                else:
                    break
            
            if timeline:
                df = pd.DataFrame(timeline)
                
                # Plot the timeline
                fig = px.line(
                    df,
                    x='Month',
                    y='Balance',
                    title='Projected Savings Growth',
                    labels={'Balance': 'Balance ($)', 'Month': 'Months'},
                )
                fig.update_layout(
                    showlegend=False,
                    yaxis_range=[0, min(max(df['Balance']), target_amount * 2)],
                    xaxis_range=[0, months]
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error("Unable to generate the savings growth timeline. Please check your input values.")
