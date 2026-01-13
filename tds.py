import streamlit as st
import pandas as pd
import json

# Set page configuration
st.set_page_config(
    page_title="TDS Calculator FY 2025-26",
    page_icon="💰",
    layout="wide"
)

# Load TDS data from the Excel file
@st.cache_data
def load_tds_data():
    file_path = 'TDS Rate Chart FY 2025-26.xlsx'
    df = pd.read_excel(file_path, sheet_name='TDS Rate Chart FY 2025-26')
    return df

# Parse rate values (handle percentages and special cases)
def parse_rate(rate_str):
    """Convert rate string to float, handling special cases"""
    if pd.isna(rate_str) or rate_str == '-' or rate_str == 'NaN':
        return None
    if isinstance(rate_str, (int, float)):
        return float(rate_str)
    
    # Handle strings like "2% (from 01-Oct-24)"
    rate_str = str(rate_str).strip()
    if '%' in rate_str:
        rate_str = rate_str.split('%')[0].strip()
    if '(' in rate_str:
        rate_str = rate_str.split('(')[0].strip()
    
    # Handle special cases
    if 'or' in rate_str.lower() or '/' in rate_str:
        # Take the first rate mentioned
        rate_str = rate_str.replace('%', '').strip()
        parts = rate_str.replace('or', '/').split('/')
        try:
            return float(parts[0].strip()) / 100
        except:
            return None
    
    try:
        return float(rate_str) / 100 if float(rate_str) > 1 else float(rate_str)
    except:
        return None

# Parse threshold values
def parse_threshold(threshold_str):
    """Convert threshold string to float, handling special formats"""
    if pd.isna(threshold_str) or threshold_str == '-':
        return None
    
    threshold_str = str(threshold_str).replace('₹', '').replace(',', '').strip()
    
    # Handle "50,000/mo" format
    if '/mo' in threshold_str:
        threshold_str = threshold_str.split('/')[0].strip()
    
    # Handle "> 1 Cr" format
    if '>' in threshold_str:
        threshold_str = threshold_str.replace('>', '').strip()
    
    # Handle ranges like "20L - 1Cr"
    if '-' in threshold_str:
        threshold_str = threshold_str.split('-')[0].strip()
    
    # Convert Lakhs and Crores
    if 'Cr' in threshold_str or 'cr' in threshold_str:
        value = float(threshold_str.replace('Cr', '').replace('cr', '').strip())
        return value * 10000000
    elif 'L' in threshold_str:
        value = float(threshold_str.replace('L', '').strip())
        return value * 100000
    
    try:
        return float(threshold_str)
    except:
        return None

# Main app
def main():
    st.title("💰 TDS Calculator - FY 2025-26")
    st.markdown("Calculate Tax Deducted at Source based on official rates for Financial Year 2025-26")
    
    # Load data
    df = load_tds_data()
    
    # Sidebar for filters
    st.sidebar.header("🔍 Search & Filter")
    
    # Search by section or description
    search_term = st.sidebar.text_input("Search by Section/Description", "")
    
    if search_term:
        filtered_df = df[df['Section - Description'].str.contains(search_term, case=False, na=False)]
    else:
        filtered_df = df
    
    # Create tabs
    tab1, tab2 = st.tabs(["📊 TDS Calculator", "📋 Rate Chart"])
    
    with tab1:
        st.header("Calculate TDS")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Section selection
            section_list = filtered_df['Section - Description'].tolist()
            selected_section = st.selectbox(
                "Select TDS Section",
                section_list,
                help="Choose the applicable TDS section"
            )
            
            # Get selected row data
            selected_row = df[df['Section - Description'] == selected_section].iloc[0]
            
            # Display threshold
            threshold = selected_row['Threshold (₹)']
            if threshold and threshold != '-':
                st.info(f"**Threshold:** {threshold}")
        
        with col2:
            # Deductee type
            deductee_type = st.radio(
                "Deductee Type",
                ["Company / Firm / Co-op / Local Authority", "Individual / HUF"],
                help="Select the type of person to whom payment is made"
            )
            
            # PAN status
            has_pan = st.checkbox("Valid PAN Available", value=True)
        
        # Amount input
        st.subheader("Enter Payment Details")
        payment_amount = st.number_input(
            "Payment Amount (₹)",
            min_value=0.0,
            value=100000.0,
            step=1000.0,
            format="%.2f"
        )
        
        # Calculate TDS
        if st.button("Calculate TDS", type="primary"):
            st.divider()
            
            # Get applicable rate
            if has_pan:
                rate = parse_rate(selected_row[deductee_type])
            else:
                rate = parse_rate(selected_row['If No/Invalid PAN'])
            
            if rate is None:
                st.error("Rate information not available for the selected combination")
            else:
                # Calculate TDS
                tds_amount = payment_amount * rate
                net_amount = payment_amount - tds_amount
                
                # Display results in a nice format
                st.success("### TDS Calculation Results")
                
                result_col1, result_col2, result_col3 = st.columns(3)
                
                with result_col1:
                    st.metric("Gross Amount", f"₹ {payment_amount:,.2f}")
                
                with result_col2:
                    st.metric(
                        "TDS Amount",
                        f"₹ {tds_amount:,.2f}",
                        delta=f"{rate*100:.2f}%"
                    )
                
                with result_col3:
                    st.metric("Net Amount", f"₹ {net_amount:,.2f}")
                
                # Show detailed breakdown
                with st.expander("📝 Detailed Breakdown"):
                    st.write(f"**Section:** {selected_section}")
                    st.write(f"**Deductee Type:** {deductee_type}")
                    st.write(f"**PAN Status:** {'Valid' if has_pan else 'Not Available/Invalid'}")
                    st.write(f"**TDS Rate:** {rate*100:.2f}%")
                    st.write(f"**Gross Amount:** ₹ {payment_amount:,.2f}")
                    st.write(f"**TDS to be Deducted:** ₹ {tds_amount:,.2f}")
                    st.write(f"**Net Payable Amount:** ₹ {net_amount:,.2f}")
                    
                    # Check threshold
                    threshold_value = parse_threshold(threshold)
                    if threshold_value:
                        if payment_amount < threshold_value:
                            st.warning(f"⚠️ Payment amount is below the threshold of ₹ {threshold_value:,.2f}. TDS may not be applicable.")
                        else:
                            st.success(f"✅ Payment amount exceeds the threshold of ₹ {threshold_value:,.2f}. TDS is applicable.")
    
    with tab2:
        st.header("Complete TDS Rate Chart FY 2025-26")
        
        # Display the full rate chart
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Section - Description": st.column_config.TextColumn(
                    "Section - Description",
                    width="large"
                ),
                "Threshold (₹)": st.column_config.TextColumn(
                    "Threshold (₹)",
                    width="medium"
                ),
                "Company / Firm / Co-op / Local Authority": st.column_config.TextColumn(
                    "Company/Firm Rate",
                    width="medium"
                ),
                "Individual / HUF": st.column_config.TextColumn(
                    "Individual/HUF Rate",
                    width="medium"
                ),
                "If No/Invalid PAN": st.column_config.TextColumn(
                    "No PAN Rate",
                    width="medium"
                )
            }
        )
        
        # Download option
        st.download_button(
            label="📥 Download Rate Chart as CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='TDS_Rate_Chart_FY_2025-26.csv',
            mime='text/csv',
        )
    
    

if __name__ == "__main__":
    main()