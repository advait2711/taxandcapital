"""
Excel Report Generator for TDS Calculator
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from io import BytesIO
from typing import List, Dict
import re


def sanitize_sheet_name(name: str) -> str:
    """Remove invalid characters from sheet name and limit length"""
    # Remove invalid characters
    invalid_chars = r'[\\/*?:\[\]]'
    sanitized = re.sub(invalid_chars, '', name)
    # Limit to 31 characters (Excel limit)
    return sanitized[:31]


def generate_excel_report(entity_name: str, pan_number: str, results: List[Dict]) -> BytesIO:
    """
    Generate Excel report with TDS calculations.
    
    Args:
        entity_name: Name of the entity
        pan_number: PAN number of the entity
        results: List of calculation result dictionaries
    
    Returns:
        BytesIO object containing the Excel file
    """
    wb = Workbook()
    
    # Remove default sheet
    if 'Sheet' in wb.sheetnames:
        del wb['Sheet']
    
    # Define styles
    header_fill = PatternFill(start_color="1E3C72", end_color="1E3C72", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    entity_fill = PatternFill(start_color="2A5298", end_color="2A5298", fill_type="solid")
    entity_font = Font(color="FFFFFF", bold=True, size=14)
    label_font = Font(bold=True, size=11)
    value_font = Font(size=11)
    currency_font = Font(size=11, bold=True, color="1E3C72")
    late_font = Font(size=11, bold=True, color="DC3545")
    ontime_font = Font(size=11, bold=True, color="28A745")
    total_fill = PatternFill(start_color="1E3C72", end_color="1E3C72", fill_type="solid")
    total_font = Font(color="FFFFFF", bold=True, size=14)
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Create a sheet for each transaction
    for idx, result in enumerate(results, 1):
        sheet_name = sanitize_sheet_name(f"Transaction_{idx}")
        ws = wb.create_sheet(title=sheet_name)
        
        # Set column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 40
        
        current_row = 1
        
        # Entity Header
        ws.merge_cells(f'A{current_row}:B{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = f"Entity Name: {entity_name}"
        cell.fill = entity_fill
        cell.font = entity_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 30
        current_row += 1
        
        # PAN Header
        ws.merge_cells(f'A{current_row}:B{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = f"PAN Number: {pan_number}"
        cell.fill = entity_fill
        cell.font = entity_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 30
        current_row += 2
        
        # Section Header
        ws.merge_cells(f'A{current_row}:B{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = "TDS CALCULATION DETAILS"
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 25
        current_row += 1
        
        # Transaction Details
        details = [
            ("TDS Section", result.get('section', '')),
            ("Description", result.get('section_description', '')),
            ("Category", result.get('category_short', '')),
            ("PAN Status", "Available" if result.get('pan_available') else "Not Available"),
            ("Transaction Amount", result.get('amount_formatted', '')),
            ("Applicable Threshold", result.get('effective_threshold_note', '')),
            ("Applicable TDS Rate", result.get('rate_display', '')),
            ("TDS Amount", result.get('tds_amount_formatted', '')),
        ]
        
        for label, value in details:
            ws[f'A{current_row}'] = label
            ws[f'A{current_row}'].font = label_font
            ws[f'A{current_row}'].border = thin_border
            ws[f'B{current_row}'] = value
            ws[f'B{current_row}'].font = currency_font if 'Amount' in label or 'Rate' in label else value_font
            ws[f'B{current_row}'].border = thin_border
            current_row += 1
        
        current_row += 1
        
        # Date Information Header
        ws.merge_cells(f'A{current_row}:B{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = "PAYMENT DUE DATE INFORMATION"
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 25
        current_row += 1
        
        date_details = [
            ("Date of Deduction", result.get('deduction_date_formatted', '')),
            ("Due Date for Payment", result.get('due_date_formatted', '')),
            ("Actual Payment Date", result.get('payment_date_formatted', '')),
            ("Payment Status", "LATE" if result.get('is_late') else "ON TIME"),
        ]
        
        for label, value in date_details:
            ws[f'A{current_row}'] = label
            ws[f'A{current_row}'].font = label_font
            ws[f'A{current_row}'].border = thin_border
            ws[f'B{current_row}'] = value
            if label == "Payment Status":
                ws[f'B{current_row}'].font = late_font if result.get('is_late') else ontime_font
            else:
                ws[f'B{current_row}'].font = value_font
            ws[f'B{current_row}'].border = thin_border
            current_row += 1
        
        # Interest section if late
        if result.get('is_late'):
            current_row += 1
            ws.merge_cells(f'A{current_row}:B{current_row}')
            cell = ws[f'A{current_row}']
            cell.value = "INTEREST CALCULATION (Section 201(1A))"
            cell.fill = PatternFill(start_color="DC3545", end_color="DC3545", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True, size=12)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            ws.row_dimensions[current_row].height = 25
            current_row += 1
            
            interest_details = [
                ("Interest Rate", "1.5% per month"),
                ("Number of Months", f"{result.get('months_late', 0)} month(s)"),
                ("Interest Amount", result.get('interest_formatted', '')),
            ]
            
            for label, value in interest_details:
                ws[f'A{current_row}'] = label
                ws[f'A{current_row}'].font = label_font
                ws[f'A{current_row}'].border = thin_border
                ws[f'B{current_row}'] = value
                ws[f'B{current_row}'].font = late_font if 'Amount' in label else value_font
                ws[f'B{current_row}'].border = thin_border
                current_row += 1
        
        current_row += 1
        
        # Total Amount
        ws.merge_cells(f'A{current_row}:B{current_row}')
        cell = ws[f'A{current_row}']
        cell.value = f"TOTAL AMOUNT PAYABLE: {result.get('total_payable_formatted', '')}"
        cell.fill = total_fill
        cell.font = total_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[current_row].height = 35
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output


def get_excel_filename(entity_name: str) -> str:
    """Generate Excel filename with entity name and date"""
    # Sanitize entity name
    safe_name = re.sub(r'[^\w\s-]', '', entity_name).strip().replace(' ', '_')
    date_str = datetime.now().strftime('%Y%m%d')
    return f"{safe_name}_Report_{date_str}.xlsx"
