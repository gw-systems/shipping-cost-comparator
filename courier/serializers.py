"""
Django REST Framework Serializers.
Converted from Pydantic V2 schemas to DRF serializers.
"""
from rest_framework import serializers
from .models import Order, OrderStatus, PaymentMode
import re


class RateRequestSerializer(serializers.Serializer):
    """Rate comparison request"""
    source_pincode = serializers.IntegerField(
        min_value=100000,
        max_value=999999,
        help_text="6-digit origin pincode"
    )
    dest_pincode = serializers.IntegerField(
        min_value=100000,
        max_value=999999,
        help_text="6-digit destination pincode"
    )
    weight = serializers.FloatField(
        min_value=0.01,
        max_value=999.99,
        help_text="Weight in kg"
    )
    is_cod = serializers.BooleanField(default=False)
    order_value = serializers.FloatField(default=0.0, min_value=0)
    mode = serializers.ChoiceField(
        choices=['Both', 'Surface', 'Air'],
        default='Both'
    )


class CostBreakdownSerializer(serializers.Serializer):
    """Cost breakdown details"""
    base_forward = serializers.FloatField()
    additional_weight = serializers.FloatField()
    cod = serializers.FloatField()
    escalation = serializers.FloatField()
    gst = serializers.FloatField()
    applied_gst_rate = serializers.CharField()
    applied_escalation_rate = serializers.CharField()


class CarrierResponseSerializer(serializers.Serializer):
    """Carrier rate response"""
    carrier = serializers.CharField()
    total_cost = serializers.FloatField()
    breakdown = CostBreakdownSerializer()
    applied_zone = serializers.CharField()
    mode = serializers.CharField()


class ZoneRatesSerializer(serializers.Serializer):
    """Zone-based rates"""
    z_a = serializers.FloatField(min_value=0.01)
    z_b = serializers.FloatField(min_value=0.01)
    z_c = serializers.FloatField(min_value=0.01)
    z_d = serializers.FloatField(min_value=0.01)
    z_f = serializers.FloatField(min_value=0.01)


class NewCarrierSerializer(serializers.Serializer):
    """New carrier creation"""
    carrier_name = serializers.CharField(min_length=1)
    mode = serializers.ChoiceField(choices=['Surface', 'Air'])
    min_weight = serializers.FloatField(min_value=0.01)
    forward_rates = ZoneRatesSerializer()
    additional_rates = ZoneRatesSerializer()
    cod_fixed = serializers.FloatField(min_value=0)
    cod_percent = serializers.FloatField(min_value=0, max_value=1)
    active = serializers.BooleanField(default=True)

    def validate_carrier_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Carrier name cannot be empty')
        return value


class OrderSerializer(serializers.ModelSerializer):
    """Order creation and updates"""

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'recipient_name', 'recipient_contact',
            'recipient_address', 'recipient_pincode', 'recipient_city',
            'recipient_state', 'recipient_phone', 'recipient_email',
            'sender_pincode', 'sender_name', 'sender_address', 'sender_phone',
            'weight', 'length', 'width', 'height', 'volumetric_weight',
            'applicable_weight', 'payment_mode', 'order_value', 'item_type',
            'sku', 'quantity', 'item_amount', 'status', 'selected_carrier',
            'total_cost', 'cost_breakdown', 'awb_number', 'zone_applied',
            'mode', 'created_at', 'updated_at', 'booked_at', 'notes'
        ]
        read_only_fields = [
            'id', 'order_number', 'volumetric_weight', 'applicable_weight',
            'created_at', 'updated_at'
        ]

    def validate_recipient_name(self, value):
        if value:
            value = value.strip()
            if not all(c.isalpha() or c in ' .-' for c in value):
                raise serializers.ValidationError(
                    'Name must contain only letters, spaces, dots, and hyphens'
                )
        return value

    def validate_recipient_contact(self, value):
        value = value.strip()
        cleaned = value.replace(' ', '').replace('-', '')
        if not cleaned.isdigit():
            raise serializers.ValidationError('Contact number must contain only digits')
        if len(cleaned) != 10:
            raise serializers.ValidationError('Contact number must be exactly 10 digits')
        return cleaned

    def validate_recipient_address(self, value):
        if value:
            value = value.strip()
            if not all(c.isalnum() or c in ' .,/-#()' for c in value):
                raise serializers.ValidationError('Address contains invalid characters')
        return value

    def validate_recipient_email(self, value):
        if value:
            value = value.strip()
            if '@' not in value or '.' not in value.split('@')[1]:
                raise serializers.ValidationError('Invalid email format')
        return value

    def validate(self, data):
        # Validate pincodes
        for field in ['recipient_pincode', 'sender_pincode']:
            if field in data:
                pincode = data[field]
                if not (100000 <= pincode <= 999999):
                    raise serializers.ValidationError({field: 'Pincode must be exactly 6 digits'})
        return data


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Partial order updates"""

    class Meta:
        model = Order
        fields = [
            'recipient_name', 'recipient_contact', 'recipient_address',
            'recipient_pincode', 'recipient_city', 'recipient_state',
            'recipient_phone', 'recipient_email', 'sender_pincode',
            'sender_name', 'sender_address', 'sender_phone', 'weight',
            'length', 'width', 'height', 'payment_mode', 'order_value',
            'item_type', 'sku', 'quantity', 'item_amount', 'notes',
            'status', 'selected_carrier', 'mode', 'zone_applied', 'total_cost'
        ]
        extra_kwargs = {field: {'required': False} for field in fields}


class CarrierSelectionSerializer(serializers.Serializer):
    """Carrier selection for booking"""
    order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    carrier_name = serializers.CharField(min_length=1)
    mode = serializers.ChoiceField(choices=['Surface', 'Air'])
