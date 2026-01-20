from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from datetime import datetime

from .tds_logic import get_all_sections_list, calculate_full_tds
from .serializers import CalculateRequestSerializer, ExcelRequestSerializer
from .excel_generator import generate_excel_report, get_excel_filename


@api_view(['GET'])
def get_sections(request):
    """Get all TDS sections for dropdown"""
    sections = get_all_sections_list()
    return Response(sections)


@api_view(['POST'])
def calculate_tds(request):
    """Calculate TDS for one or more transactions"""
    serializer = CalculateRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    entity = data['entity']
    transactions = data['transactions']
    
    results = []
    for idx, txn in enumerate(transactions, 1):
        # Convert date strings to date objects if needed
        deduction_date = txn['deduction_date']
        payment_date = txn['payment_date']
        
        if isinstance(deduction_date, str):
            deduction_date = datetime.strptime(deduction_date, '%Y-%m-%d').date()
        if isinstance(payment_date, str):
            payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        
        result = calculate_full_tds(
            section_code=txn['section_code'],
            amount=txn['amount'],
            category=txn['category'],
            pan_available=txn['pan_available'],
            deduction_date=deduction_date,
            payment_date=payment_date,
            threshold_type=txn.get('threshold_type'),
            annual_threshold_exceeded=txn.get('annual_threshold_exceeded', False),
            selected_slab=txn.get('selected_slab'),
            selected_condition=txn.get('selected_condition')
        )
        result['transaction_number'] = idx
        results.append(result)
    
    return Response({
        'entity': {
            'entity_name': entity['entity_name'],
            'pan_number': entity['pan_number']
        },
        'results': results
    })


@api_view(['POST'])
def generate_excel(request):
    """Generate Excel report for TDS calculations"""
    serializer = ExcelRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    entity = data['entity']
    results = data['results']
    
    # Generate Excel file
    excel_file = generate_excel_report(
        entity_name=entity['entity_name'],
        pan_number=entity['pan_number'],
        results=results
    )
    
    # Generate filename
    filename = get_excel_filename(entity['entity_name'])
    
    # Return as downloadable file
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
