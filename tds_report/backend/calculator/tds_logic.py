"""
TDS Calculator Logic
Financial Year 2025-2026 (Non-Salary)

This module contains the exact business logic ported from tds_calculator.py.
NO MODIFICATIONS to calculation rules, conditions, or thresholds.
"""

from datetime import date, timedelta
import calendar
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple


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


def get_section_by_code(section_code: str) -> Optional[TDSSection]:
    """Get TDS section by section code"""
    for section in TDS_SECTIONS:
        if section.section == section_code:
            return section
    return None


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


def calculate_full_tds(
    section_code: str,
    amount: float,
    category: str,
    pan_available: bool,
    deduction_date: date,
    payment_date: date,
    threshold_type: Optional[str] = None,
    annual_threshold_exceeded: bool = False,
    selected_slab: Optional[str] = None
) -> Dict:
    """
    Calculate complete TDS details for a transaction.
    Returns a dictionary with all calculation results.
    """
    section = get_section_by_code(section_code)
    if not section:
        return {"error": f"Section {section_code} not found"}
    
    # Get applicable rate
    rate, rate_display = get_applicable_rate(section, category, pan_available)
    
    # Handle sections with slabs
    if section.has_slabs and section.slabs and selected_slab:
        for slab in section.slabs:
            if slab["description"] == selected_slab:
                rate = slab["rate"]
                rate_display = f"{slab['rate']}%"
                break
    
    # Determine effective threshold
    effective_threshold = section.threshold
    effective_threshold_note = section.threshold_note
    
    if section.has_threshold_types and section.threshold_types and threshold_type:
        for t in section.threshold_types:
            if t["type"] == threshold_type:
                effective_threshold = t["threshold"]
                effective_threshold_note = t["threshold_note"]
                break
        
        # For 194C Single Transaction with annual threshold exceeded
        if section.section == "194C" and threshold_type == "Single Transaction" and annual_threshold_exceeded:
            effective_threshold = 0
            effective_threshold_note = "₹0 (Annual limit already exceeded)"
    
    # Calculate TDS
    tds_amount, above_threshold = calculate_tds(amount, rate, effective_threshold)
    
    # Calculate Due Date
    due_date = calculate_due_date(deduction_date, section)
    
    # Calculate Interest
    months, interest, is_late = calculate_interest(tds_amount, deduction_date, payment_date, due_date)
    
    # Total Payable
    total_payable = tds_amount + interest
    
    return {
        "section": section.section,
        "section_description": section.description,
        "category": category,
        "category_short": "Company/Firm/Co-op/LA" if "Company" in category else "Individual/HUF",
        "pan_available": pan_available,
        "amount": amount,
        "amount_formatted": format_indian_number(amount),
        "effective_threshold": effective_threshold,
        "effective_threshold_note": effective_threshold_note,
        "rate": rate,
        "rate_display": rate_display,
        "tds_amount": tds_amount,
        "tds_amount_formatted": format_indian_number(tds_amount),
        "above_threshold": above_threshold,
        "deduction_date": deduction_date.strftime('%Y-%m-%d'),
        "deduction_date_formatted": deduction_date.strftime('%d-%b-%Y'),
        "due_date": due_date.strftime('%Y-%m-%d'),
        "due_date_formatted": due_date.strftime('%d-%b-%Y'),
        "payment_date": payment_date.strftime('%Y-%m-%d'),
        "payment_date_formatted": payment_date.strftime('%d-%b-%Y'),
        "is_late": is_late,
        "months_late": months,
        "interest": interest,
        "interest_formatted": format_indian_number(interest),
        "total_payable": total_payable,
        "total_payable_formatted": format_indian_number(total_payable),
        "is_property_section": section.is_property_section,
        "has_threshold_types": section.has_threshold_types,
        "threshold_types": section.threshold_types,
        "has_slabs": section.has_slabs,
        "slabs": section.slabs
    }


def get_all_sections_list() -> List[Dict]:
    """Get list of all TDS sections for dropdown"""
    sections = []
    for section in TDS_SECTIONS:
        sections.append({
            "section": section.section,
            "description": section.description,
            "display_name": get_section_display_name(section),
            "threshold": section.threshold,
            "threshold_note": section.threshold_note,
            "company_rate": section.company_rate,
            "individual_rate": section.individual_rate,
            "no_pan_rate": section.no_pan_rate,
            "has_slabs": section.has_slabs,
            "slabs": section.slabs,
            "is_property_section": section.is_property_section,
            "has_threshold_types": section.has_threshold_types,
            "threshold_types": section.threshold_types
        })
    return sections
