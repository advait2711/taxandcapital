"""
TDS Calculator Web App
Financial Year 2025-2026 (Non-Salary)
Built with Streamlit

Features:
- All TDS sections with applicable rates
- Category selection (Company/Firm, Individual/HUF)
- PAN availability check
- Due date calculation
- Interest calculation under Section 201(1A)
"""

import streamlit as st
from datetime import date, timedelta
import calendar
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple

# Page Configuration
st.set_page_config(
    page_title="TDS Calculator - FY 2025-2026",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    .main-header p {
        color: #e0e0e0;
        margin: 0.5rem 0 0 0;
    }
    .result-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1e3c72;
    }
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ffc107;
    }
    .success-card {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    .danger-card {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #dc3545;
    }
    .metric-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        color: #1e3c72;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .total-box {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-top: 1rem;
    }
    .total-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .total-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .info-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .info-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #dee2e6;
    }
    .info-table td:first-child {
        font-weight: 500;
        color: #495057;
        width: 50%;
    }
    .info-table td:last-child {
        color: #1e3c72;
        font-weight: 600;
    }
    .stSelectbox [data-baseweb="select"] {
        margin-top: 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
</style>
""", unsafe_allow_html=True)


# TDS Sections Data
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


# Complete TDS Sections for FY 2025-2026
TDS_SECTIONS = [
    TDSSection("192A", "Payment of accumulated balance due to an employee", 50000, "₹50,000", None, 10, 30),
    TDSSection("193", "Interest on securities", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194", "Dividends", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194A", "Interest other than interest on securities - In any Others Case", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194A-Banks", "Banks / Co-operative society engaged in business of banking / Post Office", 50000, "₹50,000", 10, 10, 20),
    TDSSection("194A-Senior", "Interest - Senior citizen", 100000, "₹1,00,000", None, 10, 20),
    TDSSection("194B", "Winning from Lotteries or crossword puzzle, etc.", 10000, "₹10,000", 30, 10, 30),
    TDSSection("194B-proviso", "Winnings from lotteries - where consideration is insufficient", 10000, "₹10,000", 30, 30, 30),
    TDSSection("194BA", "Winnings from online games (From 01-Apr-2023)", None, "-", 30, 30, 30),
    TDSSection("194BA-Sub(2)", "Net Winnings from online games - where net winnings insufficient", None, "-", 30, 30, 30),
    TDSSection("194BB", "Winnings from Horse Race", 10000, "₹10,000", 30, 30, 30),
    TDSSection("194C", "Payment to Contractors", 100000, "₹1,00,000 (Annual)", 2, 1, 20, has_threshold_types=True,
               threshold_types=[
                   {"type": "Single Transaction", "threshold": 30000, "threshold_note": "₹30,000 (Single Transaction)"},
                   {"type": "Annual Aggregate", "threshold": 100000, "threshold_note": "₹1,00,000 (Annual)"}
               ]),
    TDSSection("194IC", "Payment under Specified agreement", None, "-", 10, 10, 20),
    TDSSection("194D", "Insurance Commission", 20000, "₹20,000", 10, 2, 20),
    TDSSection("194DA", "Payment in respect of life insurance policy (from 01.10.2014)", 100000, "₹1,00,000", 2, 2, 20, "2% (from 1st Oct 2024)", "2% (from 1st Oct 2024)"),
    TDSSection("194E", "Payment to Non-Resident Sportsmen or Sports Association", None, "-", 20, 20, 20),
    TDSSection("194EE", "Payments out of deposits under NSS", 2500, "₹2,500", 10, 10, 20),
    TDSSection("194F", "Repurchase Units by MFs", None, "-", 20, 20, 20, "20% (upto 30th Sep 2024)", "20% (upto 30th Sep 2024)"),
    TDSSection("194G", "Commission - Lottery", 20000, "₹20,000", 2, 2, 20, "2% (from 1st Oct 2024)", "2% (from 1st Oct 2024)"),
    TDSSection("194H", "Commission / Brokerage", 20000, "₹20,000", 2, 2, 20, "2% (from 1st Oct 2024)", "2% (from 1st Oct 2024)"),
    TDSSection("194I", "Rent - Land and Building/Furniture/Fittings", 50000, "₹50,000 (Per month)", 10, 10, 20),
    TDSSection("194I(a)", "Rent - Plant/Machinery/Equipment", 50000, "₹50,000 (Per month)", 2, 2, 20),
    TDSSection("194IA", "Transfer of certain immovable property other than agriculture land", 5000000, "₹50,00,000", 1, 1, 20, is_property_section=True),
    TDSSection("194IB", "Payment of rent by certain individuals or Hindu undivided family", 50000, "₹50,000", 2, 2, 20, "2% (from 1st Oct 2024)", "2% (from 1st Oct 2024)", is_property_section=True),
    TDSSection("194J(a)", "Fees for Technical Services", 50000, "₹50,000", 2, 2, 20),
    TDSSection("194J(b)", "Fees for Professional services or royalty etc.", 50000, "₹50,000", 10, 10, 20),
    TDSSection("194K", "Payment of Dividend by Mutual Funds (From 01 Apr 2020)", 10000, "₹10,000", 10, 10, 20),
    TDSSection("194LA", "Immovable Property (Compensation)", 500000, "₹5,00,000", 10, 10, 20),
    TDSSection("194LB", "Income by way of interest from infrastructure debt fund (non-resident)", None, "-", 5, 5, 20),
    TDSSection("194LBA(a)", "Certain Income in the form of interest from units of a business trust to a residential unit holder", None, "-", 10, 10, 20),
    TDSSection("194LBA(b)", "Certain Income in the form of dividend from units of a business trust to a resident unit holder", None, "-", 10, 10, 20),
    TDSSection("194LBA(1)", "Payment of the nature referred to in Section 10(23FC)(a)", None, "-", 5, 5, 20),
    TDSSection("194LBA(2)", "Payment of the nature referred to in Section 10(23FC)(b)", None, "-", 10, 10, 20),
    TDSSection("194LBA(3)", "Payment of the nature referred to in section 10(23FCA) by business trust to unit holders", None, "-", 30, 30, 35, 
               "35% - Non Residents Company, 30% - Non Residents other than companies", "30%"),
    TDSSection("194LBB", "Income in respect of units of investment fund", None, "-", 10, 10, 35,
               "35% - Non Residents Company, 30% - Non Residents other than companies, 10% - Residents",
               "10% - Residents, 30% - Non Resident"),
    TDSSection("194LBC", "Income in respect of investment in securitisation trust", None, "-", 10, 10, 35,
               "35% - Non Residents Company, 30% - Non Residents other than companies, 10% - Residents", "10%"),
    TDSSection("194LC", "Income by way of interest by an Indian specified company to a non-resident/foreign company", None, "-", 5, 5, 20,
               "5% or 4% or 9% (see conditions)", "5% or 4% or 9% (see conditions)"),
    TDSSection("194LD", "Interest on certain bonds and govt. Securities (from 01-06-2013)", None, "-", 5, 5, 20),
    TDSSection("194M", "Payment of certain sums by certain individuals or Hindu undivided family", 5000000, "₹50,00,000", 2, 2, 20, 
               "2% (from 1st Oct 2024)", "2% (from 1st Oct 2024)"),
    TDSSection("194N", "Payment of certain amounts in cash", 10000000, "Withdrawal in Excess of Rs. 1 Cr.", 2, 2, 20),
    TDSSection("194NC", "Payment of certain amounts in cash to co-operative societies not covered by first proviso", 30000000, "Withdrawal in Excess of Rs. 3 Cr. for Co-operative Society", 2, 2, 20),
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
    TDSSection("194O", "TDS on e-commerce participants (From 01-Oct-2020)", 500000, "₹5,00,000 (Individual/HUF)", 0.1, 0.1, 5,
               "0.1% (from 1st Oct 2024)", "0.1% (from 1st Oct 2024)"),
    TDSSection("194P", "TDS in case of Specified Senior Citizen", None, "-", None, None, 0, "Not Applicable", "Rates in Force"),
    TDSSection("194Q", "TDS on Purchase of Goods exceeding Rs. 50 Lakhs (From 01-July-2021)", 5000000, "In Excess of Rs. 50 Lakhs", 0.1, 0.1, 5),
    TDSSection("194R", "TDS in case any benefit or perquisite (arising from business or profession)", 20000, "₹20,000", 10, 10, 20),
    TDSSection("194R-proviso", "TDS in case any Benefits or perquisites - where benefit is provided in kind or insufficient cash", 20000, "₹20,000", 10, 10, 20),
    TDSSection("194S", "TDS on payment on transfer of Virtual Digital Asset (From 01-July-2022)", 10000, "₹10,000", 1, 1, 20),
    TDSSection("194S-proviso", "TDS on Payment for transfer of virtual digital asset - payment is in kind", 10000, "₹10,000", 1, 1, 20),
    TDSSection("194T", "Payment of salary, remuneration, commission, bonus or interest to a partner of firm", 20000, "₹20,000", 10, 10, 20),
]


def get_section_display_name(section: TDSSection) -> str:
    """Create display name for dropdown"""
    return f"{section.section} - {section.description}"


def get_applicable_rate(section: TDSSection, category: str, pan_available: bool) -> Tuple[Optional[float], str]:
    """Get applicable TDS rate based on category and PAN availability"""
    if not pan_available:
        return section.no_pan_rate, f"{section.no_pan_rate}% (No PAN)"
    
    if category == "Company / Firm / Co-operative Society / Local Authority":
        if section.company_rate is None:
            return None, "Not Applicable"
        note = section.company_rate_note if section.company_rate_note else ""
        return section.company_rate, f"{section.company_rate}% {note}".strip()
    else:  # Individual / HUF
        if section.individual_rate is None:
            return None, "Not Applicable"
        note = section.individual_rate_note if section.individual_rate_note else ""
        return section.individual_rate, f"{section.individual_rate}% {note}".strip()


def calculate_tds(amount: float, rate: Optional[float], threshold: Optional[float]) -> Tuple[float, bool]:
    """Calculate TDS amount"""
    if rate is None:
        return 0, False
    
    # Check if amount exceeds threshold
    if threshold is not None and amount < threshold:
        return 0, False  
    
    tds_amount = amount * (rate / 100)
    return round(tds_amount, 2), True


def calculate_due_date(deduction_date: date, section: TDSSection) -> date:
    """
    Calculate TDS payment due date based on rules:
    - April to February: 7th of following month
    - March: 30th April
    - 194-IA, 194-IB: 30 days from end of month
    """
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


def calculate_interest(tds_amount: float, deduction_date: date, payment_date: date, due_date: date) -> Tuple[int, float, bool]:
    """
    Calculate interest @ 1.5% per month for late payment under Section 201(1A).
    - Interest period: From month of deduction to month of payment
    - Part of a month counts as full month
    """
    is_late = payment_date > due_date
    
    if not is_late:
        return 0, 0.0, False
    
    # Count months from deduction month to payment month (inclusive)
    deduction_month = deduction_date.month + (deduction_date.year * 12)
    payment_month = payment_date.month + (payment_date.year * 12)
    
    months = payment_month - deduction_month 
    
    # Interest @ 1.5% per month
    interest = tds_amount * 0.015 * months
    
    return months, round(interest, 2), True


def format_currency(amount: float) -> str:
    """Format amount in Indian currency format"""
    if amount >= 10000000:  
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.2f}"


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
    
    # Add decimal part if exists
    decimal_part = num - int(num)
    if decimal_part > 0:
        result += f".{int(decimal_part * 100):02d}"
    
    return "₹" + result


# Main App
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧮 TDS Calculator</h1>
        <p>Financial Year 2025-2026 | Non-Salary Payments</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for Settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Category Selection
        st.subheader("Deductee Category")
        category = st.selectbox(
            "Select Category",
            [
                "Company / Firm / Co-operative Society / Local Authority",
                "Individual / HUF"
            ],
            label_visibility="collapsed"
        )
        
        # PAN Availability
        st.subheader("PAN Status")
        pan_available = st.radio(
            "Is PAN Available?",
            ["Yes", "No"],
            horizontal=True
        ) == "Yes"
        
        if not pan_available:
            st.warning("⚠️ Higher TDS rate applicable for No PAN cases")
        
        st.divider()
        
        st.markdown("""
        ### 📋 Instructions
        1. Select the TDS Section
        2. Enter the transaction amount
        3. Enter the date of deduction
        4. View calculated TDS and due date
        5. Check interest for late payment
        """)
    
    # Main Content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Transaction Details")
        
        # Section Selection - Searchable
        section_options = {get_section_display_name(s): s for s in TDS_SECTIONS}
        selected_section_name = st.selectbox(
            "Select TDS Section",
            options=list(section_options.keys()),
            help="Search and select the applicable TDS section"
        )
        selected_section = section_options[selected_section_name]
        
        # Display Section Details
        with st.expander("📖 Section Details", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Section:** {selected_section.section}")
                st.markdown(f"**Threshold:** {selected_section.threshold_note}")
            with col_b:
                rate, rate_display = get_applicable_rate(selected_section, category, pan_available)
                st.markdown(f"**Applicable Rate:** {rate_display}")
                if selected_section.is_property_section:
                    st.info("🏠 Property Section: 30-day due date rule applies")
        
        # Handle sections with threshold types (like 194C)
        selected_threshold_type = None
        effective_threshold = selected_section.threshold
        effective_threshold_note = selected_section.threshold_note
        if selected_section.has_threshold_types and selected_section.threshold_types:
            st.markdown("**Select Threshold Type:**")
            threshold_type_options = [t["type"] for t in selected_section.threshold_types]
            selected_threshold_type_name = st.selectbox("Threshold Type", threshold_type_options, label_visibility="collapsed")
            for t in selected_section.threshold_types:
                if t["type"] == selected_threshold_type_name:
                    selected_threshold_type = t
                    effective_threshold = t["threshold"]
                    effective_threshold_note = t["threshold_note"]
                    break
            st.info(f"📋 Selected: {selected_threshold_type_name} - Threshold: {effective_threshold_note}")
        
        # Handle sections with slabs
        selected_slab = None
        if selected_section.has_slabs and selected_section.slabs:
            st.markdown("**Applicable Slab:**")
            slab_options = [s["description"] for s in selected_section.slabs]
            selected_slab_desc = st.selectbox("Select Slab", slab_options)
            for slab in selected_section.slabs:
                if slab["description"] == selected_slab_desc:
                    selected_slab = slab
                    rate = slab["rate"]
                    rate_display = f"{slab['rate']}%"
                    break
        
        # Transaction Amount
        amount = st.number_input(
            "Transaction Amount (₹)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.2f",
            help="Enter the total transaction amount"
        )
        
        st.divider()
        
        # Date Inputs
        st.subheader("📅 Date Information")
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            deduction_date = st.date_input(
                "Date of Deduction",
                value=date.today(),
                help="Date when TDS was/will be deducted"
            )
        
        with col_d2:
            payment_date = st.date_input(
                "Actual Payment Date",
                value=date.today(),
                help="Date when TDS is actually paid to government"
            )
    
    with col2:
        st.subheader("📊 Quick Summary")
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Category</div>
            <div class="metric-value" style="font-size: 1rem;">{'Company/Firm' if 'Company' in category else 'Individual/HUF'}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">PAN Status</div>
            <div class="metric-value" style="font-size: 1rem; color: {'#28a745' if pan_available else '#dc3545'};">
                {'✓ Available' if pan_available else '✗ Not Available'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">TDS Rate</div>
            <div class="metric-value">{rate_display if rate is not None else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Calculate Button and Results
    st.divider()
    
    if st.button("🔢 Calculate TDS", type="primary", use_container_width=True):
        if amount <= 0:
            st.error("❌ Please enter a valid transaction amount greater than 0")
        elif rate is None:
            st.warning("⚠️ TDS is not applicable for this section and category combination")
        else:
            # Calculate TDS
            tds_amount, above_threshold = calculate_tds(amount, rate, effective_threshold)
            
            # Calculate Due Date
            due_date = calculate_due_date(deduction_date, selected_section)
            
            # Calculate Interest
            months, interest, is_late = calculate_interest(tds_amount, deduction_date, payment_date, due_date)
            
            # Total Payable
            total_payable = tds_amount + interest
            
            # Display Results
            st.markdown("---")
            st.subheader("📋 TDS Calculation Summary")
            
            # TDS Calculation Section
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("#### 💰 TDS Calculation")
                
                result_html = f"""
                <table class="info-table">
                    <tr><td>Selected TDS Section</td><td>{selected_section.section}</td></tr>
                    <tr><td>Description</td><td>{selected_section.description[:50]}...</td></tr>
                    <tr><td>Category</td><td>{'Company/Firm/Co-op/LA' if 'Company' in category else 'Individual/HUF'}</td></tr>
                    <tr><td>PAN Status</td><td>{'Available' if pan_available else 'Not Available'}</td></tr>
                    <tr><td>Transaction Amount</td><td>{format_indian_number(amount)}</td></tr>
                    <tr><td>Applicable Threshold</td><td>{effective_threshold_note}</td></tr>
                    <tr><td>Applicable TDS Rate</td><td>{rate_display}</td></tr>
                    <tr><td><strong>TDS Amount</strong></td><td><strong>{format_indian_number(tds_amount)}</strong></td></tr>
                </table>
                """
                st.markdown(result_html, unsafe_allow_html=True)
                
                if not above_threshold and effective_threshold is not None:
                    st.info(f"ℹ️ Amount is below threshold of {effective_threshold_note}. No TDS applicable.")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_r2:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("#### 📅 Payment Due Date")
                
                due_date_html = f"""
                <table class="info-table">
                    <tr><td>Date of Deduction</td><td>{deduction_date.strftime('%d-%b-%Y')}</td></tr>
                    <tr><td>Due Date for Payment</td><td><strong>{due_date.strftime('%d-%b-%Y')}</strong></td></tr>
                    <tr><td>Actual Payment Date</td><td>{payment_date.strftime('%d-%b-%Y')}</td></tr>
                    <tr><td>Payment Status</td><td style="color: {'#dc3545' if is_late else '#28a745'};">
                        {'⚠️ LATE' if is_late else '✓ ON TIME'}
                    </td></tr>
                </table>
                """
                st.markdown(due_date_html, unsafe_allow_html=True)
                
                if selected_section.is_property_section:
                    st.info("🏠 Property Section: Due date is 30 days from end of deduction month")
                elif deduction_date.month == 3:
                    st.info("📅 March Deduction: Extended due date of 30th April applies")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Interest Calculation Section
            if is_late:
                st.markdown('<div class="danger-card">', unsafe_allow_html=True)
                st.markdown("#### ⚠️ Interest Calculation (Section 201(1A))")
                
                # Month breakdown
                deduction_month_name = deduction_date.strftime('%B %Y')
                payment_month_name = payment_date.strftime('%B %Y')
                
                interest_html = f"""
                <table class="info-table">
                    <tr><td>Interest Rate</td><td>1.5% per month</td></tr>
                    <tr><td>Period: From</td><td>{deduction_month_name} (Month of Deduction)</td></tr>
                    <tr><td>Period: To</td><td>{payment_month_name} (Month of Payment)</td></tr>
                    <tr><td>Number of Months</td><td><strong>{months} month(s)</strong></td></tr>
                    <tr><td>Calculation</td><td>{format_indian_number(tds_amount)} × 1.5% × {months}</td></tr>
                    <tr><td><strong>Interest Amount</strong></td><td><strong style="color: #dc3545;">{format_indian_number(interest)}</strong></td></tr>
                </table>
                """
                st.markdown(interest_html, unsafe_allow_html=True)
                
                st.warning(f"""
                **Note:** Interest is calculated from the month of deduction to the month of payment. 
                Even a single day delay in a new month is counted as a full month.
                """)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="success-card">', unsafe_allow_html=True)
                st.markdown("#### ✅ No Interest Applicable")
                st.markdown("Payment is on or before the due date. No interest under Section 201(1A).")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Total Amount Payable
            st.markdown(f"""
            <div class="total-box">
                <div class="total-label">TOTAL AMOUNT PAYABLE</div>
                <div class="total-value">{format_indian_number(total_payable)}</div>
                <div style="font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem;">
                    (TDS: {format_indian_number(tds_amount)} {'+ Interest: ' + format_indian_number(interest) if interest > 0 else ''})
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed Breakdown
            with st.expander("📊 View Detailed Breakdown"):
                st.markdown("### Complete Calculation Details")
                
                breakdown_data = {
                    "Parameter": [
                        "TDS Section",
                        "Section Description",
                        "Deductee Category",
                        "PAN Availability",
                        "Transaction Amount",
                        "Applicable Threshold",
                        "Applicable TDS Rate",
                        "TDS Amount",
                        "Date of Deduction",
                        "Statutory Due Date",
                        "Actual Payment Date",
                        "Payment Status",
                        "Months for Interest",
                        "Interest Rate",
                        "Interest Amount",
                        "Total Amount Payable"
                    ],
                    "Value": [
                        selected_section.section,
                        selected_section.description,
                        category,
                        "Yes" if pan_available else "No",
                        format_indian_number(amount),
                        effective_threshold_note,
                        rate_display,
                        format_indian_number(tds_amount),
                        deduction_date.strftime('%d-%b-%Y'),
                        due_date.strftime('%d-%b-%Y'),
                        payment_date.strftime('%d-%b-%Y'),
                        "LATE" if is_late else "ON TIME",
                        str(months) if is_late else "N/A",
                        "1.5% per month" if is_late else "N/A",
                        format_indian_number(interest) if is_late else "₹0.00",
                        format_indian_number(total_payable)
                    ]
                }
                
                st.table(breakdown_data)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>📌 <strong>Disclaimer:</strong> This calculator is for informational purposes only. 
        Please consult a tax professional for specific advice.</p>
        <p>💡 Based on TDS rates applicable for FY 2025-2026 (Non-Salary Payments)</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
