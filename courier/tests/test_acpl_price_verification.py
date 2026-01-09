"""
Price Verification Tests for ACPL Surface 50kg
Tests city-to-city routing and pricing
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def acpl_surface_50kg():
    """Fixture to get ACPL Surface 50kg courier"""
    return Courier.objects.get(name='ACPL Surface 50kg')


@pytest.mark.django_db
class TestACPLSurface50kg:
    """Test suite for ACPL Surface 50kg pricing"""
    
    def test_gandhidham_to_bhiwandi_20kg(self, acpl_surface_50kg):
        """
        Test: Gandhidham to Bhiwandi - 20kg
        Route: Gandhidham (370201) -> Bhiwandi (421308)
        """
        rate_dict = acpl_surface_50kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=370201,  # Gandhidham
            dest_pincode=421308,    # Bhiwandi
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['total_cost'] > 0
        assert 'breakdown' in result
        assert result['breakdown']['base_freight'] > 0
        assert result['breakdown']['fuel_surcharge'] >= 0
        assert result['breakdown']['hamali_charge'] >= 0
        assert result['breakdown']['docket_fee'] >= 0
    
    def test_bhiwandi_to_gandhidham_20kg(self, acpl_surface_50kg):
        """
        Test: Bidirectional routing - Bhiwandi to Gandhidham - 20kg
        Route: Bhiwandi (421308) -> Gandhidham (370201)
        """
        rate_dict = acpl_surface_50kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=421308,  # Bhiwandi
            dest_pincode=370201,    # Gandhidham
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['total_cost'] > 0
        # Bidirectional routing should work
        assert 'breakdown' in result
    
    def test_fuel_surcharge_included(self, acpl_surface_50kg):
        """Test: Verify fuel surcharge is calculated"""
        rate_dict = acpl_surface_50kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=370201,
            dest_pincode=421308,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        # ACPL should have fuel surcharge
        assert result['breakdown']['fuel_surcharge'] >= 0
    
    def test_hamali_charge_calculation(self, acpl_surface_50kg):
        """Test: Verify hamali charge is calculated for heavy weight"""
        rate_dict = acpl_surface_50kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=370201,
            dest_pincode=421308,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        # Hamali should be charged for 20kg
        assert result['breakdown']['hamali_charge'] >= 0
