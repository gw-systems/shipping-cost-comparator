import pytest
from rest_framework.exceptions import ValidationError
from courier.serializers import (
    RateRequestSerializer,
    NewCarrierSerializer,
     CarrierResponseSerializer
)

class TestRateRequestSerializer:
    def test_valid_data(self):
        data = {
            "source_pincode": 400001,
            "dest_pincode": 110001,
            "weight": 10.5,
            "is_cod": True,
            "order_value": 5000,
            "mode": "Surface"
        }
        serializer = RateRequestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["source_pincode"] == 400001

    def test_invalid_pincode_min(self):
        data = {
            "source_pincode": 100, # Too short
            "dest_pincode": 110001,
            "weight": 10.5
        }
        serializer = RateRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_pincode" in serializer.errors

    def test_invalid_pincode_max(self):
        data = {
            "source_pincode": 1000000, # Too long
            "dest_pincode": 110001,
            "weight": 10.5
        }
        serializer = RateRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_pincode" in serializer.errors

    def test_invalid_weight(self):
        data = {
            "source_pincode": 400001,
            "dest_pincode": 110001,
            "weight": -5 # Invalid
        }
        serializer = RateRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "weight" in serializer.errors

class TestNewCarrierSerializer:
    def test_valid_carrier(self):
        data = {
            "carrier_name": "Test Carrier",
            "mode": "Surface",
            "min_weight": 0.5,
            "forward_rates": {
                "z_a": 10, "z_b": 20, "z_c": 30, "z_d": 40, "z_f": 50
            },
            "additional_rates": {
                "z_a": 5, "z_b": 5, "z_c": 5, "z_d": 5, "z_f": 5
            },
            "cod_fixed": 30,
            "cod_percent": 0.02,
            "active": True
        }
        serializer = NewCarrierSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_empty_carrier_name(self):
        data = {
            "carrier_name": "   ",
            "mode": "Surface"
        }
        serializer = NewCarrierSerializer(data=data)
        assert not serializer.is_valid()
        assert "carrier_name" in serializer.errors
