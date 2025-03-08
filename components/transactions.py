import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_transactions(db):
    st.title("Transaction Management")

    # Tabs for different transaction types
    tab1, tab2 = st.tabs(["Single Transaction", "Recurring Transaction"])

    with tab1:
        # Single Transaction Form
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("Date", datetime.now())
                type = st.selectbox("Type", ["Income", "Expense"])

            with col2:
                amount = st.number_input("Amount", min_value=0.01, format="%.2f")
                categories = db.get_all_categories()
                category_list = categories[categories['type'] == type]['name'].tolist()
                category = st.selectbox("Category", category_list)

            description = st.text_input("Description")
            tags = st.text_input("Tags (comma-separated)", help="Add tags to better organize your transactions")

            if st.form_submit_button("Add Transaction"):
                try:
                    db.add_transaction(
                        date.strftime("%Y-%m-%d"),
                        type,
                        category,
                        amount,
                        description,
                        tags.split(',') if tags else []
                    )
                    st.success("Transaction added successfully!")
                except Exception as e:
                    st.error(f"Error adding transaction: {str(e)}")

    with tab2:
        # Recurring Transaction Form
        with st.form("recurring_transaction_form"):
            name = st.text_input("Transaction Name", help="A name to identify this recurring transaction")

            col1, col2 = st.columns(2)
            with col1:
                r_type = st.selectbox("Type", ["Income", "Expense"], key="recurring_type")
                r_amount = st.number_input("Amount", min_value=0.01, format="%.2f", key="recurring_amount")

            with col2:
                categories = db.get_all_categories()
                category_list = categories[categories['type'] == r_type]['name'].tolist()
                r_category = st.selectbox("Category", category_list, key="recurring_category")
                frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Yearly"])

            r_description = st.text_input("Description", key="recurring_description")
            r_tags = st.text_input("Tags (comma-separated)", help="Add tags to better organize your transactions", key="recurring_tags")

            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("Start Date", datetime.now())
            with col4:
                end_date = st.date_input("End Date (Optional)", None)

            if st.form_submit_button("Set Up Recurring Transaction"):
                try:
                    db.add_recurring_transaction(
                        name,
                        r_type,
                        r_category,
                        r_amount,
                        r_description,
                        frequency,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d") if end_date else None,
                        r_tags.split(',') if r_tags else []
                    )
                    st.success("Recurring transaction set up successfully!")
                except Exception as e:
                    st.error(f"Error setting up recurring transaction: {str(e)}")

    # Transaction Filters
    st.subheader("Transaction History")

    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search description or tags", "")
    with col2:
        filter_type = st.multiselect("Filter by type", ["Income", "Expense"])
    with col3:
        all_categories = db.get_all_categories()
        filter_category = st.multiselect("Filter by category", all_categories['name'].unique().tolist())

    # Date range filter
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start date", datetime.now() - timedelta(days=30))
    with date_col2:
        end_date = st.date_input("End date", datetime.now())

    # Get and filter transactions
    transactions = db.get_transactions()
    if not transactions.empty:
        # Apply filters
        mask = (transactions['date'].dt.date >= start_date) & (transactions['date'].dt.date <= end_date)
        if search_term:
            mask &= (
                transactions['description'].str.contains(search_term, case=False, na=False) |
                transactions['tags'].apply(lambda x: any(search_term.lower() in tag.lower() for tag in x))
            )
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
        def style_type(val):
            return 'color: green' if val == 'Income' else 'color: red'

        styled_df = filtered_transactions[['date', 'type', 'category', 'amount', 'description', 'tags']].copy()
        styled_df['amount'] = styled_df['amount'].apply(lambda x: f"${x:,.2f}")
        styled_df['tags'] = styled_df['tags'].apply(lambda x: ', '.join(x) if x else '')

        st.dataframe(
            styled_df.style.map(style_type, subset=['type']),
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

        # Show transaction statistics
        st.subheader("Transaction Statistics")
        stat_tab1, stat_tab2 = st.tabs(["Category Analysis", "Time Analysis"])

        with stat_tab1:
            cat_data = filtered_transactions.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
            cat_data.columns = ['Category', 'Total Amount', 'Number of Transactions']
            st.dataframe(
                cat_data.style.format({'Total Amount': '${:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )

        with stat_tab2:
            time_data = filtered_transactions.groupby(filtered_transactions['date'].dt.strftime('%Y-%m'))['amount'].sum()
            st.line_chart(time_data)
    else:
        st.info("No transactions recorded yet.")

    # Custom Categories Management
    st.subheader("Manage Categories")
    with st.form("category_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            cat_name = st.text_input("Category Name")
        with col2:
            cat_type = st.selectbox("Category Type", ["Income", "Expense"])
        with col3:
            cat_color = st.color_picker("Category Color", "#1976D2")

        if st.form_submit_button("Add Custom Category"):
            if cat_name.strip():
                if db.add_custom_category(cat_name, cat_type, color=cat_color):
                    st.success(f"Added new category: {cat_name}")
                else:
                    st.error("Category already exists!")
            else:
                st.error("Category name cannot be empty!")