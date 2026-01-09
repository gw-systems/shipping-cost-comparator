"""
Price Verification Tests for Delhivery Courier Services
Tests various weight categories and zone combinations using pytest framework
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def delhivery_surface_05kg():
    """Fixture to get Delhivery Surface 0.5kg courier"""
    return Courier.objects.get(name='Delhivery Surface 0.5kg')


class TestDelhiverySurface05kg:
    """Test suite for Delhivery Surface 0.5kg pricing"""
    
    def test_zone_a_metro_to_metro_2kg(self, delhivery_surface_05kg):
        """
        Test: Zone A (Metro to Metro) - 2kg
        Route: Mumbai (400001) -> Delhi (110001)
        Expected: Base freight Rs 105 (27 + 26*3)
        """
        # Step 1: Get Rate Dict
        rate_dict = delhivery_surface_05kg.get_rate_dict()

        # Step 2: Calculate Cost
        result = calculate_cost(
            weight=2,
            source_pincode=400001,  # Mumbai (Metro)
            dest_pincode=110001,    # Delhi (Metro)
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['zone_id'] == 'z_a'
        assert result['breakdown']['base_freight'] == 105.0
        assert result['breakdown']['charged_weight'] == 2.0
        assert result['total_cost'] > 0
    
    def test_zone_b_regional_2kg(self, delhivery_surface_05kg):
        """
        Test: Zone B (Regional - Same State) - 2kg
        Route: Mumbai (400001) -> Nagpur (440001)
        Expected: Base freight Rs 126 (30 + 32*3)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,  # Mumbai, Maharashtra
            dest_pincode=440001,    # Nagpur, Maharashtra (Non-Metro)
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['zone_id'] == 'z_b'
        assert result['breakdown']['base_freight'] == 126.0
        assert result['total_cost'] > 0
    
    def test_zone_c_intercity_2kg(self, delhivery_surface_05kg):
        """
        Test: Zone C (Intercity - Different States) - 2kg
        Route: Mumbai (400001) -> Jaipur (302001)
        Expected: Base freight Rs 144 (36 + 36*3)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,  # Mumbai, Maharashtra
            dest_pincode=302001,    # Jaipur, Rajasthan
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['zone_id'] == 'z_c'
        assert result['breakdown']['base_freight'] == 144.0
        assert result['total_cost'] > 0
    

    def test_zone_e_northeast_2kg(self, delhivery_surface_05kg):
        """
        Test: Zone E (North-East) - 2kg
        Route: Mumbai (400001) -> Guwahati (781001)
        Expected: Base freight Rs 270 (69 + 67*3)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,  # Mumbai, Maharashtra
            dest_pincode=781001,    # Guwahati, Assam
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['zone_id'] in ['z_e', 'z_f']  # North-East states
        assert result['breakdown']['base_freight'] == 270.0
        assert result['total_cost'] > 0
    
    def test_zone_a_with_cod_2kg(self, delhivery_surface_05kg):
        """
        Test: Zone A with COD - 2kg
        Route: Mumbai (400001) -> Delhi (110001)
        Order Value: Rs 1000
        Expected: COD charge Rs 44 (29 fixed + 1.5% of 1000)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,  # Mumbai (Metro)
            dest_pincode=110001,    # Delhi (Metro)
            carrier_data=rate_dict,
            is_cod=True,
            order_value=1000
        )
        
        assert result['serviceable'] == True
        assert result['zone_id'] == 'z_a'
        assert result['breakdown']['cod_charge'] == 44.0  # 29 + 15
        assert result['total_cost'] == 194.41  # Verified calculation
    
    def test_weight_calculation_05kg(self, delhivery_surface_05kg):
        """
        Test: Verify weight calculation for 0.5kg increments
        Weight: 0.5kg should charge for 1 unit (forward rate only)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=0.5,
            source_pincode=400001,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['charged_weight'] == 0.5
        assert result['breakdown']['base_freight'] == 27.0  # Forward rate only
    
    def test_weight_calculation_1kg(self, delhivery_surface_05kg):
        """
        Test: Verify weight calculation for 1kg
        Weight: 1kg = 2 units (forward + 1 additional)
        """
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=1,
            source_pincode=400001,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['charged_weight'] == 1.0
        assert result['breakdown']['base_freight'] == 53.0  # 27 + 26
    
    def test_gst_calculation(self, delhivery_surface_05kg):
        """Test: Verify GST is calculated at 18%"""
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        breakdown = result['breakdown']
        expected_gst = round(breakdown['amount_before_tax'] * 0.18, 2)
        assert abs(breakdown['gst_amount'] - expected_gst) < 0.01  # Allow small rounding difference
    
    def test_profit_margin_calculation(self, delhivery_surface_05kg):
        """Test: Verify profit margin is calculated at 15%"""
        rate_dict = delhivery_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=2,
            source_pincode=400001,
            dest_pincode=110001,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        breakdown = result['breakdown']
        expected_profit = round(breakdown['courier_payable'] * 0.15, 2)
        assert abs(breakdown['profit_margin'] - expected_profit) < 0.01
