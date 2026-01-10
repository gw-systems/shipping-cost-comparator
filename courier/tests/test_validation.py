
import pytest
from courier.engine import CostCalculator
from courier.exceptions import InvalidWeightError

class TestInputValidation:
    def test_negative_weight_raises_error(self):
        """Test that negative weight raises InvalidWeightError"""
        carrier_data = {"carrier_name": "Test", "min_weight": 0}
        with pytest.raises(InvalidWeightError):
            CostCalculator(weight=-1, source_pincode=400001, dest_pincode=110001, carrier_data=carrier_data)
            
    def test_zero_weight_raises_error(self):
        """Test that zero weight raises InvalidWeightError"""
        carrier_data = {"carrier_name": "Test", "min_weight": 0}
        with pytest.raises(InvalidWeightError):
            CostCalculator(weight=0, source_pincode=400001, dest_pincode=110001, carrier_data=carrier_data)

    def test_valid_weight_passes(self):
        """Test that positive weight does not raise error"""
        carrier_data = {"carrier_name": "Test", "min_weight": 0}
        try:
            CostCalculator(weight=0.5, source_pincode=400001, dest_pincode=110001, carrier_data=carrier_data)
        except InvalidWeightError:
            pytest.fail("Valid weight raised InvalidWeightError")
