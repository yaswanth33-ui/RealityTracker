import streamlit as st
from datetime import datetime

def render_transactions(db):
    st.title("Transaction Management")
    
    # Transaction Form
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            type = st.selectbox("Type", ["Income", "Expense"])
            
        with col2:
            amount = st.number_input("Amount", min_value=0.01, format="%.2f")
            category = st.selectbox(
                "Category",
                ["Salary", "Investment", "Food", "Transport", "Housing", "Utilities", "Entertainment", "Other"]
            )
            
        description = st.text_input("Description")
        
        if st.form_submit_button("Add Transaction"):
            try:
                db.add_transaction(
                    date.strftime("%Y-%m-%d"),
                    type,
                    category,
                    amount,
                    description
                )
                st.success("Transaction added successfully!")
            except Exception as e:
                st.error(f"Error adding transaction: {str(e)}")

    # Transaction History
    st.subheader("Transaction History")
    transactions = db.get_transactions()
    if not transactions.empty:
        transactions['date'] = pd.to_datetime(transactions['date'])
        transactions = transactions.sort_values('date', ascending=False)
        
        st.dataframe(
            transactions[['date', 'type', 'category', 'amount', 'description']],
            use_container_width=True
        )
    else:
        st.info("No transactions recorded yet.")
