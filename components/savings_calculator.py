
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def calculate_monthly_savings(target_amount, current_savings, months, interest_rate):
    """Calculate required monthly savings to reach goal"""
    if months <= 0 or target_amount <= current_savings:
        return 0
    r = interest_rate / 100 / 12  # Monthly interest rate
    if r == 0:
        return (target_amount - current_savings) / months
    try:
        pmt = np.pmt(r, months, -current_savings, target_amount, when='end')
        return 0 if np.isinf(pmt) or np.isnan(pmt) else float(pmt)
    except:
        return 0

def render_savings_calculator():
    st.title("Savings Goal Calculator")
    
    with st.expander("📖 How to Adjust Parameters", expanded=True):
        st.markdown("""
        **Guidelines for Parameter Adjustment:**
        
        1. **Target Amount** ($1,000+):
           - For emergency fund: 3-6 months of expenses
           - For major purchase: Full cost + 10% buffer
           - For retirement: Based on desired annual income × years
        
        2. **Current Savings** ($0+):
           - Enter your current balance
           - Should be less than target amount
           - Include all relevant savings/investments
        
        3. **Time Frame** (0.1-50 years):
           - Short-term: 1-3 years
           - Medium-term: 3-10 years
           - Long-term: 10+ years
           - Longer time = Lower monthly payments
        
        4. **Interest Rate** (0-30%):
           - Savings Account: 1-2%
           - High-yield Savings: 3-5%
           - Conservative Investment: 6-8%
           - Moderate Investment: 8-12%
        
        *Tip: If calculation fails, try increasing the time frame or reducing the target amount.*
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_amount = st.number_input("Target Amount ($)", min_value=1000.0, value=50000.0, step=1000.0)
        current_savings = st.number_input("Current Savings ($)", min_value=0.0, value=5000.0, step=1000.0)
    
    with col2:
        years = st.number_input("Time Frame (Years)", min_value=0.1, max_value=50.0, value=5.0, step=0.5)
        interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.1)
    
    if st.button("Calculate Savings Plan", type="primary"):
        if target_amount <= current_savings:
            st.success("You have already reached your savings goal!")
            return
            
        months = int(years * 12)
        monthly_savings = calculate_monthly_savings(target_amount, current_savings, months, interest_rate)
        
        if target_amount <= 0:
            st.error("Target amount must be greater than zero")
            return
            
        if years <= 0:
            st.error("Time frame must be greater than zero")
            return
            
        if monthly_savings <= 0:
            st.warning(f"""
            The calculation is not possible with these parameters. This could be because:
            - The target amount (${target_amount:,.2f}) is too close to current savings (${current_savings:,.2f})
            - The time frame ({years:.1f} years) is too short
            - The interest rate ({interest_rate:.1f}%) is too high
            
            Try adjusting these values to make the calculation possible.
            """)
            return
            
        total_contributions = monthly_savings * months
        interest_earned = target_amount - current_savings - total_contributions
        
        st.markdown("---")
    
        # Results display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Required Monthly Savings", f"${monthly_savings:.2f}")
        with col2:
            st.metric("Total Contributions", f"${total_contributions:.2f}")
        with col3:
            st.metric("Interest Earned", f"${interest_earned:.2f}")
    
        # Progress timeline
        st.subheader("Savings Growth Timeline")
        
        try:
            timeline = []
            balance = current_savings
            
            for month in range(months + 1):
                if month <= months:  # Only plot within the specified timeframe
                    timeline.append({
                        'Month': month,
                        'Balance': round(balance, 2)
                    })
                    interest = balance * (interest_rate / 100 / 12)
                    balance = balance + interest + monthly_savings
            
            if timeline:
                df = pd.DataFrame(timeline)
                
                # Ensure values are finite
                df['Balance'] = df['Balance'].clip(lower=0, upper=target_amount * 1.2)
                
                fig = px.line(
                    df,
                    x='Month',
                    y='Balance',
                    title='Projected Savings Growth',
                    labels={'Balance': 'Balance ($)', 'Month': 'Months'},
                )
                fig.update_layout(
                    showlegend=False,
                    yaxis=dict(
                        range=[0, df['Balance'].max() * 1.1],
                        tickformat='$,.0f'
                    ),
                    xaxis=dict(
                        range=[0, months],
                        tickmode='linear',
                        dtick=max(1, months // 10)
                    ),
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Unable to generate the savings growth timeline. Error: {str(e)}")
