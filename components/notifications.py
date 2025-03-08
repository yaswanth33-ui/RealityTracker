
import streamlit as st
import pandas as pd
from datetime import datetime

def check_budget_alerts(db):
    """Check for budget overages and return alerts"""
    budget_goals = db.get_budget_goals()
    transactions = db.get_transactions()
    alerts = []
    
    if not budget_goals.empty and not transactions.empty:
        current_month = datetime.now().strftime("%Y-%m")
        monthly_expenses = transactions[
            (transactions['type'] == 'Expense') &
            (transactions['date'].dt.strftime("%Y-%m") == current_month)
        ].groupby('category')['amount'].sum()
        
        for _, row in budget_goals.iterrows():
            actual = monthly_expenses.get(row['category'], 0)
            percentage = (actual / row['amount'] * 100) if row['amount'] > 0 else 0
            
            # Alert at 80%, 90% and over 100%
            if percentage >= 100:
                alerts.append({
                    'category': row['category'],
                    'severity': 'high',
                    'message': f"🚨 OVER BUDGET: {row['category']} (${actual:.2f} / ${row['amount']:.2f})",
                    'percentage': percentage
                })
            elif percentage >= 90:
                alerts.append({
                    'category': row['category'],
                    'severity': 'medium',
                    'message': f"⚠️ WARNING: {row['category']} at {percentage:.1f}% of budget",
                    'percentage': percentage
                })
            elif percentage >= 80:
                alerts.append({
                    'category': row['category'],
                    'severity': 'low',
                    'message': f"ℹ️ NOTICE: {row['category']} at {percentage:.1f}% of budget",
                    'percentage': percentage
                })
    
    return alerts

def render_alerts(alerts):
    """Render alerts in the UI"""
    if not alerts:
        return
    
    # Sort alerts by severity
    sorted_alerts = sorted(alerts, key=lambda x: (
        0 if x['severity'] == 'high' else 
        1 if x['severity'] == 'medium' else 2
    ))
    
    for alert in sorted_alerts:
        if alert.get('balanced', False):
            st.markdown(f'<div class="stAlert alert-balanced">{alert["message"]}</div>', unsafe_allow_html=True)
        elif alert['severity'] == 'high':
            st.markdown(f'<div class="stAlert alert-danger">{alert["message"]}</div>', unsafe_allow_html=True)
        elif alert['severity'] == 'medium':
            st.markdown(f'<div class="stAlert alert-warning">{alert["message"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="stAlert alert-info">{alert["message"]}</div>', unsafe_allow_html=True)

def check_financial_goal_alerts(db):
    """Check for financial goals deadline alerts"""
    financial_goals = db.get_financial_goals()
    alerts = []
    
    if not financial_goals.empty:
        for _, goal in financial_goals.iterrows():
            days_left = (pd.to_datetime(goal['target_date']) - pd.Timestamp.now()).days
            progress = (goal['current_amount'] / goal['target_amount']) * 100
            
            # Alert for goals approaching deadline
            if days_left <= 7 and days_left > 0:
                alerts.append({
                    'name': goal['name'],
                    'severity': 'medium',
                    'message': f"⏰ DEADLINE APPROACHING: {goal['name']} due in {days_left} days ({progress:.1f}% complete)",
                    'days_left': days_left
                })
            elif days_left <= 0:
                alerts.append({
                    'name': goal['name'],
                    'severity': 'high',
                    'message': f"⚠️ DEADLINE PASSED: {goal['name']} is overdue ({progress:.1f}% complete)",
                    'days_left': days_left
                })
            
            # Alert for goals with slow progress
            time_elapsed = (pd.Timestamp.now() - pd.to_datetime(goal['created_at'])).days
            total_time = (pd.to_datetime(goal['target_date']) - pd.to_datetime(goal['created_at'])).days
            
            if total_time > 0:
                expected_progress = (time_elapsed / total_time) * 100
                if progress < (expected_progress * 0.7) and time_elapsed > 30:
                    alerts.append({
                        'name': goal['name'],
                        'severity': 'medium',
                        'message': f"📉 SLOW PROGRESS: {goal['name']} is behind schedule ({progress:.1f}% vs expected {expected_progress:.1f}%)",
                        'progress_gap': expected_progress - progress
                    })
    
    return alerts
