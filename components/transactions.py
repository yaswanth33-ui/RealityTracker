import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_category_badge(icon, name, color):
    st.markdown(
        f"""
        <div style="
            display: inline-flex;
            align-items: center;
            background-color: {color}20;
            padding: 4px 8px;
            border-radius: 12px;
            margin: 2px;
        ">
            <span style="margin-right: 4px">{icon}</span>
            <span style="color: {color}">{name}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def get_filtered_categories(db, transaction_type):
    categories = db.get_all_categories()
    return categories[categories['type'] == transaction_type]

def render_transactions(db):
    st.title("Transaction Management")

    # Initialize session state for transaction type
    if 'transaction_type' not in st.session_state:
        st.session_state.transaction_type = "Income"

    # Tabs for different transaction types
    tab1, tab2, tab3 = st.tabs(["Single Transaction", "Recurring Transaction", "Categories"])

    with tab1:
        # Single Transaction Form
        with st.form("transaction_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("Date", datetime.now())
                # Update transaction type in session state when changed
                transaction_type = st.selectbox(
                    "Type",
                    ["Income", "Expense"],
                    key="transaction_type_select"
                )
                st.session_state.transaction_type = transaction_type

            with col2:
                amount = st.number_input("Amount", min_value=0.01, format="%.2f")

                # Get filtered categories based on current transaction type
                filtered_categories = get_filtered_categories(db, st.session_state.transaction_type)

                category = st.selectbox(
                    "Category",
                    filtered_categories['name'].tolist(),
                    format_func=lambda x: f"{filtered_categories[filtered_categories['name'] == x]['icon'].iloc[0]} {x}",
                    key=f"category_select_{st.session_state.transaction_type}"  # Dynamic key based on type
                )

            description = st.text_input("Description")
            tags = st.text_input("Tags (comma-separated)", help="Add tags to better organize your transactions")

            if st.form_submit_button("Add Transaction"):
                try:
                    db.add_transaction(
                        date.strftime("%Y-%m-%d"),
                        transaction_type,
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
        with st.form("recurring_transaction_form", clear_on_submit=True):
            name = st.text_input("Transaction Name", help="A name to identify this recurring transaction")

            col1, col2 = st.columns(2)
            with col1:
                r_type = st.selectbox("Type", ["Income", "Expense"], key="recurring_type")
                r_amount = st.number_input("Amount", min_value=0.01, format="%.2f", key="recurring_amount")

            with col2:
                # Get filtered categories based on type
                filtered_categories = get_filtered_categories(db, r_type)

                r_category = st.selectbox(
                    "Category",
                    filtered_categories['name'].tolist(),
                    format_func=lambda x: f"{filtered_categories[filtered_categories['name'] == x]['icon'].iloc[0]} {x}",
                    key="recurring_category"
                )
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

    with tab3:
        st.subheader("Category Management")

        # Display existing categories
        st.write("### Default Categories")
        categories = db.get_all_categories() # Removed reliance on session state here.

        col1, col2 = st.columns(2)
        with col1:
            st.write("Income Categories")
            income_categories = categories[categories['type'] == 'Income']
            for _, cat in income_categories.iterrows():
                render_category_badge(cat['icon'], cat['name'], cat['color'])

        with col2:
            st.write("Expense Categories")
            expense_categories = categories[categories['type'] == 'Expense']
            for _, cat in expense_categories.iterrows():
                render_category_badge(cat['icon'], cat['name'], cat['color'])

        # Add custom category form
        st.write("### Add Custom Category")
        with st.form("category_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                cat_name = st.text_input("Category Name")
            with col2:
                cat_type = st.selectbox("Category Type", ["Income", "Expense"])
            with col3:
                cat_icon = st.text_input("Icon (emoji)", "💫")

            cat_color = st.color_picker("Category Color", "#1976D2")
            cat_description = st.text_area("Description (optional)")

            if st.form_submit_button("Add Custom Category"):
                if validate_category(cat_name, cat_type, cat_icon, cat_color, cat_description):
                    if db.add_custom_category(cat_name, cat_type, cat_icon, cat_color, cat_description):
                        st.success(f"Added new category: {cat_icon} {cat_name}")
                        # Update session state categories - not needed here anymore
                        st.experimental_rerun()
                    else:
                        st.error("Category already exists!")

    # Transaction History
    st.markdown("---")
    st.subheader("Transaction History")

    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("Search description or tags", "")
    with col2:
        filter_type = st.multiselect("Filter by type", ["Income", "Expense"])
    with col3:
        filter_category = st.multiselect("Filter by category", categories['name'].unique().tolist()) #Use db.get_all_categories() here

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

def validate_category(name, type, icon, color, description):
    if not name.strip():
        st.error("Category name cannot be empty")
        return False
    if not icon.strip():
        st.error("Please select an icon")
        return False
    if len(name) > 50:
        st.error("Category name is too long (maximum 50 characters)")
        return False
    return True