
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io

def render_data_operations(db):
    st.title("Data Import/Export")
    
    tab1, tab2 = st.tabs(["Export Data", "Import Data"])
    
    with tab1:
        st.header("Export Data")
        
        # Get data
        transactions = db.get_transactions()
        if not transactions.empty:
            # Format selection
            export_format = st.selectbox(
                "Select Export Format",
                ["CSV", "Excel", "JSON"],
                key="export_format"
            )
            
            # Date range filter
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", transactions['date'].min())
            with col2:
                end_date = st.date_input("End Date", transactions['date'].max())
            
            # Filter data
            mask = (transactions['date'].dt.date >= start_date) & (transactions['date'].dt.date <= end_date)
            filtered_data = transactions[mask].copy()
            
            if not filtered_data.empty:
                # Prepare data for export
                export_data = filtered_data.copy()
                export_data['date'] = export_data['date'].dt.strftime('%Y-%m-%d')
                
                if export_format == "CSV":
                    data = export_data.to_csv(index=False)
                    mime = "text/csv"
                    ext = "csv"
                elif export_format == "Excel":
                    buffer = io.BytesIO()
                    export_data.to_excel(buffer, index=False)
                    data = buffer.getvalue()
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ext = "xlsx"
                else:  # JSON
                    data = export_data.to_json(orient='records', date_format='iso')
                    mime = "application/json"
                    ext = "json"
                
                st.download_button(
                    f"Download {export_format}",
                    data=data,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.{ext}",
                    mime=mime
                )
        else:
            st.info("No transactions available to export.")
    
    with tab2:
        st.header("Import Data")
        
        import_format = st.selectbox(
            "Select Import Format",
            ["CSV", "Excel", "JSON"],
            key="import_format"
        )
        
        uploaded_file = st.file_uploader(
            f"Upload {import_format} file",
            type=[import_format.lower()],
            help=f"Upload a {import_format} file containing transactions"
        )
        
        if uploaded_file is not None:
            try:
                if import_format == "CSV":
                    data = pd.read_csv(uploaded_file)
                elif import_format == "Excel":
                    data = pd.read_excel(uploaded_file)
                else:  # JSON
                    data = pd.read_json(uploaded_file)
                
                # Validate required columns
                required_columns = ['date', 'type', 'category', 'amount', 'description']
                if not all(col in data.columns for col in required_columns):
                    st.error("File must contain columns: date, type, category, amount, description")
                    return
                
                # Preview data
                st.subheader("Preview")
                st.dataframe(data.head())
                
                if st.button("Import Data", type="primary"):
                    for _, row in data.iterrows():
                        try:
                            db.add_transaction(
                                date=row['date'],
                                type=row['type'],
                                category=row['category'],
                                amount=float(row['amount']),
                                description=row['description'],
                                tags=row.get('tags', [])
                            )
                    except Exception as e:
                        st.error(f"Error importing row: {str(e)}")
                        continue
                    
                    st.success(f"Successfully imported {len(data)} transactions!")
                    
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
