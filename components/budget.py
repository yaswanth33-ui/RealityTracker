import streamlit as st
import plotly.express as px

def render_budget(db):
    st.title("Budget Planning")
    
    # Budget Goal Setting
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox(
                "Category",
                ["Food", "Transport", "Housing", "Utilities", "Entertainment", "Other"]
            )
            
        with col2:
            amount = st.number_input("Monthly Budget Amount", min_value=0.01, format="%.2f")
            
        if st.form_submit_button("Set Budget"):
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
        transactions['date'] = pd.to_datetime(transactions['date'])
        current_month = datetime.now().strftime("%Y-%m")
        monthly_expenses = transactions[
            (transactions['type'] == 'Expense') &
            (transactions['date'].dt.strftime("%Y-%m") == current_month)
        ].groupby('category')['amount'].sum()

        comparison_data = []
        for _, row in budget_goals.iterrows():
            actual = monthly_expenses.get(row['category'], 0)
            comparison_data.append({
                'category': row['category'],
                'Budget': row['amount'],
                'Actual': actual,
                'Remaining': max(row['amount'] - actual, 0)
            })

        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            fig = px.bar(
                df_comparison,
                x='category',
                y=['Budget', 'Actual'],
                title='Budget vs Actual Spending by Category',
                barmode='group',
                color_discrete_map={'Budget': '#2E7D32', 'Actual': '#1976D2'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Set budget goals and add transactions to see your budget analysis!")
