import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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

    # Transaction Filters
    st.subheader("Transaction History")

    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search description", "")
    with col2:
        filter_type = st.multiselect("Filter by type", ["Income", "Expense"])
    with col3:
        filter_category = st.multiselect("Filter by category", 
            ["Salary", "Investment", "Food", "Transport", "Housing", "Utilities", "Entertainment", "Other"])

    # Date range filter
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
    with date_col2:
        end_date = st.date_input("End date", datetime.now())

    # Get and filter transactions
    transactions = db.get_transactions()
    if not transactions.empty:
        transactions['date'] = pd.to_datetime(transactions['date'])

        # Apply filters
        mask = (transactions['date'].dt.date >= start_date) & (transactions['date'].dt.date <= end_date)
        if search_term:
            mask &= transactions['description'].str.contains(search_term, case=False, na=False)
        if filter_type:
            mask &= transactions['type'].isin(filter_type)
        if filter_category:
            mask &= transactions['category'].isin(filter_category)

        filtered_transactions = transactions[mask].sort_values('date', ascending=False)

        # Display transaction stats
        total_income = filtered_transactions[filtered_transactions['type'] == 'Income']['amount'].sum()
        total_expenses = filtered_transactions[filtered_transactions['type'] == 'Expense']['amount'].sum()

        stats_col1, stats_col2, stats_col3 = st.columns(3)
        with stats_col1:
            st.metric("Filtered Income", f"${total_income:,.2f}")
        with stats_col2:
            st.metric("Filtered Expenses", f"${total_expenses:,.2f}")
        with stats_col3:
            st.metric("Net Amount", f"${total_income - total_expenses:,.2f}")

        # Display transactions with formatting
        st.dataframe(
            filtered_transactions[['date', 'type', 'category', 'amount', 'description']].style
            .format({'amount': '${:,.2f}'})
            .applymap(lambda x: 'color: green' if x == 'Income' else 'color: red', subset=['type']),
            use_container_width=True,
            hide_index=True
        )

        # Export functionality
        if st.button("Export to CSV"):
            csv = filtered_transactions.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No transactions recorded yet.")