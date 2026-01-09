"""
Price Verification Tests for Blue Dart
Tests region-based pricing with EDL charges
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def bluedart():
    """Fixture to get Blue Dart courier"""
    return Courier.objects.get(name='Blue Dart')


@pytest.mark.django_db
class TestBlueDart:
    """Test suite for Blue Dart pricing"""
    
    def test_bhiwandi_to_delhi_20kg(self, bluedart):
        """
        Test: Bhiwandi to Delhi - 20kg
        Route: Bhiwandi (421308) -> Delhi (110001)
        """
        rate_dict = bluedart.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,  # Bhiwandi
            dest_pincode=110001,    # Delhi
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['total_cost'] > 0
        assert 'breakdown' in result
        assert result['breakdown']['base_freight'] > 0
        assert 'zone' in result['breakdown']
    
    def test_edl_charge_calculation(self, bluedart):
        """Test: Verify EDL (Extended Delivery Location) charge if applicable"""
        rate_dict = bluedart.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        # EDL charge may or may not be present depending on location
        assert 'edl_charge' in result['breakdown']
    
    def test_fuel_surcharge_calculation(self, bluedart):
        """Test: Verify fuel surcharge is calculated (typically 55.6%)"""
        rate_dict = bluedart.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['fuel_surcharge'] > 0
        # Fuel surcharge should be significant for Blue Dart
    
    def test_awb_docket_fee(self, bluedart):
        """Test: Verify AWB/Docket fee is included"""
        rate_dict = bluedart.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['docket_fee'] >= 0
    
    def test_region_based_pricing(self, bluedart):
        """Test: Verify region-based pricing is used"""
        rate_dict = bluedart.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        # Zone should be a region name (e.g., NORTH, SOUTH, etc.)
        assert result['breakdown']['zone'] is not None

    def test_dod_charge(self, bluedart):
        """
        Test: Verify DOD (Draft on Delivery) charge.
        Since DOD fields are not yet in FeeStructure model, we inject config manually.
        """
        rate_dict = bluedart.get_rate_dict()
        
        # Inject DOD config into variable_fees
        rate_dict['variable_fees']['dod_charge'] = {
            'percent': 0.005,  # 0.5%
            'min_amount': 200.0
        }
        
        # DOD logic: Max(Value * 0.5%, Min 200)
        # Case 1: Value 10000. 0.5% = 50. Max(50, 200) = 200.
        result = calculate_cost(
            weight=5,
            source_pincode=421308,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=True,
            order_value=10000
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['dod_charge'] == 200.0
        # When DOD is present, standard COD fee should be 0 (based on engine logic)
        assert result['breakdown']['cod_charge'] == 0
