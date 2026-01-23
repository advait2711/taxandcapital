"""
Bulk TDS Calculator Web App
Financial Year 2025-2026 (Non-Salary)
Built with Streamlit

Features:
- Excel file upload for bulk TDS calculation
- Section reference tab with all TDS sections
- PAN-based category auto-detection
- Due date calculation
- Status determination (Taxable/Under Threshold)
- Download results as Excel
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import calendar
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import io

# Page Configuration
st.set_page_config(
    page_title="Bulk TDS Calculator - FY 2025-2026",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)




# ============== TDS LOGIC (from tds_logic.py) ==============

# PAN 4th character to category mapping
PAN_CATEGORY_MAP = {
    'P': 'Individual / HUF',
    'H': 'Individual / HUF',
    'C': 'Company / Firm / Co-operative Society / Local Authority',
    'F': 'Company / Firm / Co-operative Society / Local Authority',
    'G': 'Company / Firm / Co-operative Society / Local Authority',
    'L': 'Company / Firm / Co-operative Society / Local Authority',
    'J': 'Company / Firm / Co-operative Society / Local Authority',
    'A': 'Company / Firm / Co-operative Society / Local Authority',
    'B': 'Company / Firm / Co-operative Society / Local Authority',
    'T': 'Company / Firm / Co-operative Society / Local Authority',
}


def detect_category_from_pan(pan: str) -> Optional[str]:
    """Detect deductee category from PAN's 4th character."""
    if not pan or len(pan) < 4:
        return None
    fourth_char = pan[3].upper()
    return PAN_CATEGORY_MAP.get(fourth_char)


def validate_pan_format(pan: str) -> bool:
    """Validate PAN format."""
    import re
    if not pan:
        return False
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan.upper()))


@dataclass
class TDSSection:
    section: str
    description: str
    threshold: Optional[float]
    threshold_note: str
    company_rate: Optional[float]
    individual_rate: Optional[float]
    no_pan_rate: float
    company_rate_note: str = ""
    individual_rate_note: str = ""
    has_slabs: bool = False
    slabs: Optional[List[Dict]] = None
    is_property_section: bool = False
    has_threshold_types: bool = False
    threshold_types: Optional[List[Dict]] = None
    has_conditions: bool = False
    conditions: Optional[List[Dict]] = None
    tds_on_excess: bool = False


# Complete TDS Sections for FY 2025-2026
TDS_SECTIONS = [
    TDSSection("192A", "Payment of accumulated balance due to an employee", 50000, "₹50,000", None, 10, 30),
    TDSSection("193", "Interest on securities", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194", "Dividends", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194A", "Interest other than interest on securities - In any Others Case", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194A-Banks", "Banks / Co-operative society engaged in business of banking / Post Office", 50000, "₹50,000", 10, 10, 20),
    TDSSection("194A-Senior", "Interest - Senior citizen", 100000, "₹1,00,000", None, 10, 20),
    TDSSection("194B", "Winning from Lotteries or crossword puzzle, etc.", 10000, "₹10,000", 30, 30, 30),
    TDSSection("194B-proviso", "Winnings from lotteries - where consideration is insufficient", 10000, "₹10,000", 30, 30, 30),
    TDSSection("194BA", "Winnings from online games (From 01-Apr-2023)", None, "-", 30, 30, 30),
    TDSSection("194BA-Sub(2)", "Net Winnings from online games - where net winnings insufficient", None, "-", 30, 30, 30),
    TDSSection("194BB", "Winnings from Horse Race", 10000, "₹10,000", 30, 30, 30),
    TDSSection("194C", "Payment to Contractors (Annual Aggregate)", 100000, "₹1,00,000 (Annual)", 2, 1, 20, has_threshold_types=True,
               threshold_types=[
                   {"type": "Single Transaction", "threshold": 30000, "threshold_note": "₹30,000 (Single Transaction)"},
                   {"type": "Annual Aggregate", "threshold": 100000, "threshold_note": "₹1,00,000 (Annual)"}
               ]),
    TDSSection("194C-Single", "Payment to Contractors (Single Transaction ≥ ₹30,000)", 30000, "₹30,000 (Single)", 2, 1, 20),
    TDSSection("194IC", "Payment under Specified agreement", None, "-", 10, 10, 20),
    TDSSection("194D", "Insurance Commission", 20000, "₹20,000", 10, 2, 20),
    TDSSection("194DA", "Payment in respect of life insurance policy (from 01.10.2014)", 100000, "₹1,00,000", 2, 2, 20),
    TDSSection("194E", "Payment to Non-Resident Sportsmen or Sports Association", None, "-", 20, 20, 20),
    TDSSection("194EE", "Payments out of deposits under NSS", 2500, "₹2,500", 10, 10, 20),
    TDSSection("194F", "Repurchase Units by MFs", None, "-", 20, 20, 20),
    TDSSection("194G", "Commission - Lottery", 20000, "₹20,000", 2, 2, 20),
    TDSSection("194H", "Commission / Brokerage", 20000, "₹20,000", 2, 2, 20),
    TDSSection("194I", "Rent - Land and Building/Furniture/Fittings", 50000, "₹50,000 (Per month)", 10, 10, 20),
    TDSSection("194I(a)", "Rent - Plant/Machinery/Equipment", 50000, "₹50,000 (Per month)", 2, 2, 20),
    TDSSection("194IA", "Transfer of certain immovable property other than agriculture land", 5000000, "₹50,00,000", 1, 1, 20, is_property_section=True),
    TDSSection("194IB", "Payment of rent by certain individuals or Hindu undivided family", 50000, "₹50,000", 2, 2, 20, is_property_section=True),
    TDSSection("194J(a)", "Fees for Technical Services", 50000, "₹50,000", 2, 2, 20),
    TDSSection("194J(b)", "Fees for Professional services or royalty etc.", 50000, "₹50,000", 10, 10, 20),
    TDSSection("194K", "Payment of Dividend by Mutual Funds (From 01 Apr 2020)", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194LA", "Immovable Property (Compensation)", 500000, "₹5,00,000", 10, 10, 20),
    TDSSection("194LB", "Income by way of interest from infrastructure debt fund (non-resident)", None, "-", 5, 5, 20),
    TDSSection("194LBA(a)", "Certain Income in the form of interest from units of a business trust to a residential unit holder", None, "-", 10, 10, 20),
    TDSSection("194LBA(b)", "Certain Income in the form of dividend from units of a business trust to a resident unit holder", None, "-", 10, 10, 20),
    TDSSection("194LBA(1)", "Payment of the nature referred to in Section 10(23FC)(a)", None, "-", 5, 5, 20),
    TDSSection("194LBA(2)", "Payment of the nature referred to in Section 10(23FC)(b)", None, "-", 10, 10, 20),
    TDSSection("194LBA(3)", "Payment of the nature referred to in section 10(23FCA) by business trust to unit holders (Resident)", None, "-", 30, 30, 35),
    TDSSection("194LBB", "Income in respect of units of investment fund (Resident)", None, "-", 10, 10, 35),
    TDSSection("194LBC", "Income in respect of investment in securitisation trust (Resident)", None, "-", 10, 10, 35),
    TDSSection("194LC", "Income by way of interest by an Indian specified company to a non-resident/foreign company", None, "-", 5, 5, 20),
    TDSSection("194LD", "Interest on certain bonds and govt. Securities (from 01-06-2013)", None, "-", 5, 5, 20),
    TDSSection("194M", "Payment of certain sums by certain individuals or Hindu undivided family", 5000000, "₹50,00,000", 2, 2, 20),
    TDSSection("194N", "Payment of certain amounts in cash", 10000000, "Withdrawal in Excess of Rs. 1 Cr.", 2, 2, 20, tds_on_excess=True),
    TDSSection("194NC", "Payment of certain amounts in cash to co-operative societies not covered by first proviso", 30000000, "Withdrawal in Excess of Rs. 3 Cr. for Co-operative Society", 2, 2, 20, tds_on_excess=True),
    TDSSection("194NF", "Payment of certain amounts in cash to non-filers", None, "Slabs", None, None, 0, has_slabs=True,
               slabs=[
                   {"description": "Exceed 20 Lacs but does not exceed 1 Cr", "rate": 2},
                   {"description": "Withdrawal in Excess of Rs. 1 Cr", "rate": 5}
               ]),
    TDSSection("194NFT", "Payment of certain amount in cash to non-filers being co-operative societies", None, "Slabs", None, None, 20, has_slabs=True,
               slabs=[
                   {"description": "Exceed 20 Lacs but does not exceed 3 Cr", "rate": 2},
                   {"description": "Withdrawal in Excess of Rs. 3 Cr", "rate": 5}
               ]),
    TDSSection("194O", "TDS on e-commerce participants (From 01-Oct-2020)", 500000, "₹5,00,000 (Individual/HUF)", 0.1, 0.1, 5),
    TDSSection("194P", "TDS in case of Specified Senior Citizen", None, "-", None, None, 0),
    TDSSection("194Q", "TDS on Purchase of Goods exceeding Rs. 50 Lakhs (From 01-July-2021)", 5000000, "In Excess of Rs. 50 Lakhs", 0.1, 0.1, 5, tds_on_excess=True),
    TDSSection("194Q-Exceed", "TDS on Purchase of Goods (Threshold already exceeded)", None, "Full Amount (Threshold Exceeded)", 0.1, 0.1, 5, tds_on_excess=False),
    TDSSection("194R", "TDS in case any benefit or perquisite (arising from business or profession)", 20000, "₹20,000", 10, 10, 20),
    TDSSection("194R-proviso", "TDS in case any Benefits or perquisites - where benefit is provided in kind or insufficient cash", 20000, "₹20,000", 10, 10, 20),
    TDSSection("194S", "TDS on payment on transfer of Virtual Digital Asset (From 01-July-2022)", 10000, "₹10,000", 1, 1, 20),
    TDSSection("194S-proviso", "TDS on Payment for transfer of virtual digital asset - payment is in kind", 10000, "₹10,000", 1, 1, 20),
    TDSSection("194T", "Payment of salary, remuneration, commission, bonus or interest to a partner of firm", 20000, "₹20,000", 10, 10, 20),
]


def get_section_by_code(section_code: str) -> Optional[TDSSection]:
    """Get TDS section by section code"""
    for section in TDS_SECTIONS:
        if section.section.upper() == section_code.upper():
            return section
    return None


def get_applicable_rate(section: TDSSection, category: str, pan_available: bool) -> Tuple[Optional[float], str]:
    """Get applicable TDS rate based on category and PAN availability"""
    if not pan_available:
        return section.no_pan_rate, f"{section.no_pan_rate}%"
    
    if category and "Company" in category:
        if section.company_rate is None:
            return None, "Not Applicable"
        return section.company_rate, f"{section.company_rate}%"
    else:
        if section.individual_rate is None:
            return None, "Not Applicable"
        return section.individual_rate, f"{section.individual_rate}%"


def calculate_tds(amount: float, rate: Optional[float], threshold: Optional[float], tds_on_excess: bool = False) -> Tuple[float, bool, str]:
    """Calculate TDS amount and return (tds_amount, above_threshold, status)"""
    if rate is None:
        return 0, False, "Not Applicable"
    
    # Check if amount exceeds threshold
    if threshold is not None and amount < threshold:
        return 0, False, "Under Threshold"
    
    # Calculate taxable amount
    if tds_on_excess and threshold is not None:
        taxable_amount = amount - threshold
    else:
        taxable_amount = amount
    
    tds_amount = taxable_amount * (rate / 100)
    return round(tds_amount, 2), True, "Taxable"


def calculate_due_date(deduction_date: date, section: TDSSection) -> date:
    """Calculate TDS payment due date"""
    month = deduction_date.month
    year = deduction_date.year
    
    # Special sections: 194-IA, 194-IB (30 days from end of month)
    if section.is_property_section:
        last_day = calendar.monthrange(year, month)[1]
        month_end = date(year, month, last_day)
        return month_end + timedelta(days=30)
    
    # March deductions - due by 30th April
    if month == 3:
        return date(year, 4, 30)
    
    # April to February - 7th of following month
    if month == 12:
        return date(year + 1, 1, 7)
    else:
        return date(year, month + 1, 7)


def format_indian_number(num: float) -> str:
    """Format number in Indian numbering system"""
    num = round(num, 2)
    s = str(int(num))
    if len(s) <= 3:
        result = s
    else:
        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + ',' + result
            s = s[:-2]
    
    decimal_part = num - int(num)
    if decimal_part > 0:
        result += f".{int(decimal_part * 100):02d}"
    
    return "₹" + result


def process_bulk_tds(df: pd.DataFrame) -> pd.DataFrame:
    """Process bulk TDS calculations from uploaded DataFrame"""
    results = []
    
    for idx, row in df.iterrows():
        try:
            # Extract data
            deductee_name = str(row.get('Deductee Name', '')).strip()
            deductee_pan = str(row.get('Deductee PAN', '')).strip().upper()
            section_code = str(row.get('TDS Section', '')).strip()
            
            # Handle amount
            amount_val = row.get('Transaction Amount', 0)
            if pd.isna(amount_val):
                amount = 0
            else:
                amount = float(amount_val)
            
            # Handle date
            date_val = row.get('Date of Deduction')
            if pd.isna(date_val):
                deduction_date = date.today()
            elif isinstance(date_val, (datetime, date)):
                deduction_date = date_val if isinstance(date_val, date) else date_val.date()
            else:
                try:
                    deduction_date = pd.to_datetime(date_val).date()
                except:
                    deduction_date = date.today()
            
            # Detect category from PAN
            pan_available = bool(deductee_pan) and validate_pan_format(deductee_pan)
            category = detect_category_from_pan(deductee_pan) if pan_available else "Individual / HUF"
            category_short = "Company/Firm" if category and "Company" in category else "Individual/HUF"
            
            # Get section
            section = get_section_by_code(section_code)
            
            if not section:
                results.append({
                    'Deductee Name': deductee_name,
                    'Deductee PAN': deductee_pan if deductee_pan else "Not Provided",
                    'Detected Category': category_short,
                    'TDS Section': section_code,
                    'Transaction Amount': amount,
                    'Applicable TDS Rate': "N/A",
                    'TDS Amount': 0,
                    'Date of Deduction': deduction_date.strftime('%d-%b-%Y'),
                    'Due Date for Payment': "N/A",
                    'Status': f"Invalid Section Code: {section_code}"
                })
                continue
            
            # Get applicable rate
            rate, rate_display = get_applicable_rate(section, category, pan_available)
            
            # Calculate TDS
            tds_amount, above_threshold, status = calculate_tds(
                amount, rate, section.threshold, section.tds_on_excess
            )
            
            # Calculate due date
            due_date = calculate_due_date(deduction_date, section)
            
            results.append({
                'Deductee Name': deductee_name,
                'Deductee PAN': deductee_pan if deductee_pan else "Not Provided",
                'Detected Category': category_short,
                'TDS Section': section.section,
                'Transaction Amount': amount,
                'Applicable TDS Rate': rate_display,
                'TDS Amount': tds_amount,
                'Date of Deduction': deduction_date.strftime('%d-%b-%Y'),
                'Due Date for Payment': due_date.strftime('%d-%b-%Y'),
                'Status': status
            })
            
        except Exception as e:
            results.append({
                'Deductee Name': str(row.get('Deductee Name', '')),
                'Deductee PAN': str(row.get('Deductee PAN', '')),
                'Detected Category': "Error",
                'TDS Section': str(row.get('TDS Section', '')),
                'Transaction Amount': 0,
                'Applicable TDS Rate': "Error",
                'TDS Amount': 0,
                'Date of Deduction': "Error",
                'Due Date for Payment': "Error",
                'Status': f"Processing Error: {str(e)}"
            })
    
    return pd.DataFrame(results)


def get_section_reference_df() -> pd.DataFrame:
    """Get DataFrame with all TDS section references"""
    data = []
    for section in TDS_SECTIONS:
        special_notes = []
        if section.has_threshold_types:
            special_notes.append("Multiple Threshold Types")
        if section.has_slabs:
            special_notes.append("Slab-based")
        if section.has_conditions:
            special_notes.append("Conditional Rates")
        if section.tds_on_excess:
            special_notes.append("TDS on Excess Amount")
        if section.is_property_section:
            special_notes.append("Property (30-day due date)")
        
        data.append({
            'Section Code': section.section,
            'Description': section.description,
            'Threshold': section.threshold_note,
            'Company/Firm Rate': f"{section.company_rate}%" if section.company_rate is not None else "N/A",
            'Individual/HUF Rate': f"{section.individual_rate}%" if section.individual_rate is not None else "N/A",
            'No PAN Rate': f"{section.no_pan_rate}%",
            'Special Notes': ", ".join(special_notes) if special_notes else "-"
        })
    
    return pd.DataFrame(data)


# ============== MAIN APP ==============

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Bulk TDS Calculator</h1>
        <p>Financial Year 2025-2026 | Upload Excel for Bulk TDS Calculation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 TDS Section Reference", "📤 Bulk TDS Calculator"])
    
    # ============== TAB 1: Section Reference ==============
    with tab1:
        st.markdown("### TDS Sections Reference - FY 2025-2026")
        st.markdown("""
        <div class="info-box">
            <strong>ℹ️ How to use:</strong> Use the exact <strong>Section Code</strong> from this table in your Excel file.
            For sections with special classifications, use the specific code (e.g., <code>194C-Single</code>, <code>194J(a)</code>, <code>194Q-Exceed</code>).
        </div>
        """, unsafe_allow_html=True)
        
        # Search filter
        search = st.text_input("🔍 Search sections by code or description", "")
        
        # Get section reference DataFrame
        section_df = get_section_reference_df()
        
        # Apply search filter
        if search:
            mask = (
                section_df['Section Code'].str.contains(search, case=False, na=False) |
                section_df['Description'].str.contains(search, case=False, na=False)
            )
            section_df = section_df[mask]
        
        # Display section table
        st.dataframe(
            section_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        # Special sections info
        st.markdown("### ⚠️ Sections with Special Classifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **194C - Payment to Contractors:**
            - `194C` - Annual Aggregate (₹1,00,000)
            - `194C-Single` - Single Transaction (₹30,000)
            
            **194J - Fees/Services:**
            - `194J(a)` - Technical Services (2%)
            - `194J(b)` - Professional Services (10%)
            """)
        
        with col2:
            st.markdown("""
            **194Q - Purchase of Goods:**
            - `194Q` - TDS on excess of ₹50 Lakhs
            - `194Q-Exceed` - Full amount (threshold already exceeded)
            
            **194N/194NC - Cash Withdrawal:**
            - TDS only on amount exceeding threshold
            """)
    
    # ============== TAB 2: Bulk Calculator ==============
    with tab2:
        st.markdown("### Upload Excel File for Bulk TDS Calculation")
        
        # Expected format info
        st.markdown("""
        <div class="info-box">
            <strong>📄 Expected Excel Format:</strong><br>
            Your Excel file must contain the following columns (exact header names):
            <ul>
                <li><strong>Deductee Name</strong> - Name of the deductee</li>
                <li><strong>Deductee PAN</strong> - PAN number (leave empty if not available)</li>
                <li><strong>TDS Section</strong> - Section code (e.g., 194C, 194J(a), 194Q-Exceed)</li>
                <li><strong>Transaction Amount</strong> - Transaction amount in ₹</li>
                <li><strong>Date of Deduction</strong> - Date of TDS deduction</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Download sample template
        sample_data = {
            'Deductee Name': ['ABC Corporation', 'John Doe', 'XYZ Ltd', 'No PAN Person'],
            'Deductee PAN': ['ABCPD1234E', 'BXYPJ5678K', 'XYZPF9012L', ''],
            'TDS Section': ['194C', '194J(b)', '194Q-Exceed', '194A'],
            'Transaction Amount': [150000, 75000, 600000, 50000],
            'Date of Deduction': ['2026-01-15', '2026-01-20', '2026-01-10', '2026-01-05']
        }
        sample_df = pd.DataFrame(sample_data)
        
        buffer = io.BytesIO()
        sample_df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        st.download_button(
            label="📥 Download Sample Template",
            data=buffer,
            file_name="tds_bulk_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.divider()
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload your Excel file",
            type=['xlsx', 'xls'],
            help="Upload an Excel file with the required columns"
        )
        
        if uploaded_file is not None:
            try:
                # Read Excel file
                df = pd.read_excel(uploaded_file)
                
                # Validate required columns
                required_columns = ['Deductee Name', 'Deductee PAN', 'TDS Section', 'Transaction Amount', 'Date of Deduction']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    st.markdown("Please ensure your Excel file has all the required column headers.")
                else:
                    # Show preview of uploaded data
                    with st.expander("📋 Preview Uploaded Data", expanded=True):
                        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                        st.caption(f"Showing first 10 of {len(df)} rows")
                    
                    # Process button
                    if st.button("🧮 Calculate TDS", type="primary", use_container_width=True):
                        with st.spinner("Processing TDS calculations..."):
                            result_df = process_bulk_tds(df)
                        
                        # Show results
                        st.markdown("### ✅ TDS Calculation Results")
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        total_transactions = len(result_df)
                        taxable_count = len(result_df[result_df['Status'] == 'Taxable'])
                        under_threshold_count = len(result_df[result_df['Status'] == 'Under Threshold'])
                        total_tds = result_df['TDS Amount'].sum()
                        
                        with col1:
                            st.metric("Total Transactions", total_transactions)
                        with col2:
                            st.metric("Taxable", taxable_count)
                        with col3:
                            st.metric("Under Threshold", under_threshold_count)
                        with col4:
                            st.metric("Total TDS", format_indian_number(total_tds))
                        
                        st.divider()
                        
                        # Results table
                        st.dataframe(
                            result_df,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                        
                        # Download results
                        st.divider()
                        
                        result_buffer = io.BytesIO()
                        result_df.to_excel(result_buffer, index=False, engine='openpyxl')
                        result_buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Download Results as Excel",
                            data=result_buffer,
                            file_name=f"tds_calculation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        
                        # Store results in session state for persistence
                        st.session_state['last_results'] = result_df
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                st.markdown("Please ensure your file is a valid Excel file (.xlsx or .xls)")
        
        # Show last results if available
        elif 'last_results' in st.session_state:
            st.info("ℹ️ Showing results from last calculation. Upload a new file to calculate again.")
            result_df = st.session_state['last_results']
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_transactions = len(result_df)
            taxable_count = len(result_df[result_df['Status'] == 'Taxable'])
            under_threshold_count = len(result_df[result_df['Status'] == 'Under Threshold'])
            total_tds = result_df['TDS Amount'].sum()
            
            with col1:
                st.metric("Total Transactions", total_transactions)
            with col2:
                st.metric("Taxable", taxable_count)
            with col3:
                st.metric("Under Threshold", under_threshold_count)
            with col4:
                st.metric("Total TDS", format_indian_number(total_tds))
            
            st.dataframe(result_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
