from rest_framework import serializers
from datetime import datetime


class TransactionSerializer(serializers.Serializer):
    """Serializer for a single transaction"""
    section_code = serializers.CharField(max_length=20)
    amount = serializers.FloatField(min_value=0)
    category = serializers.ChoiceField(choices=[
        ("Company / Firm / Co-operative Society / Local Authority", "Company / Firm / Co-operative Society / Local Authority"),
        ("Individual / HUF", "Individual / HUF")
    ])
    pan_available = serializers.BooleanField()
    deduction_date = serializers.DateField()
    payment_date = serializers.DateField()
    threshold_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    annual_threshold_exceeded = serializers.BooleanField(required=False, default=False)
    selected_slab = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)


class EntitySerializer(serializers.Serializer):
    """Serializer for entity details"""
    entity_name = serializers.CharField(max_length=200)
    pan_number = serializers.CharField(max_length=10)
    
    def validate_pan_number(self, value):
        """Validate PAN format: 5 letters + 4 digits + 1 letter"""
        import re
        value = value.upper()
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', value):
            raise serializers.ValidationError("Invalid PAN format. Expected: ABCDE1234F")
        return value


class CalculateRequestSerializer(serializers.Serializer):
    """Serializer for TDS calculation request"""
    entity = EntitySerializer()
    transactions = TransactionSerializer(many=True)
    
    def validate_transactions(self, value):
        if not value:
            raise serializers.ValidationError("At least one transaction is required")
        return value


class ExcelRequestSerializer(serializers.Serializer):
    """Serializer for Excel generation request"""
    entity = EntitySerializer()
    results = serializers.ListField(child=serializers.DictField())
