"""
Price Verification Tests for Shadowfax Surface 0.5kg
Tests zonal pricing and cost calculations
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def shadowfax_surface_05kg():
    """Fixture to get Shadowfax Surface 0.5kg courier"""
    return Courier.objects.get(name='Shadowfax Surface 0.5kg')


@pytest.mark.django_db
class TestShadowfaxSurface05kg:
    """Test suite for Shadowfax Surface 0.5kg pricing"""
    
    def test_basic_pricing_20kg(self, shadowfax_surface_05kg):
        """
        Test: Basic pricing calculation - 20kg
        Route: 504273 -> 400075
        """
        rate_dict = shadowfax_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=504273,
            dest_pincode=400075,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['total_cost'] > 0
        assert 'breakdown' in result
        assert result['breakdown']['base_freight'] > 0
        assert result['breakdown']['charged_weight'] == 20.0
    
    def test_zone_identification(self, shadowfax_surface_05kg):
        """Test: Verify zone is correctly identified"""
        rate_dict = shadowfax_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=504273,
            dest_pincode=400075,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert 'zone' in result['breakdown']
        # zone_id should be the code, breakdown['zone'] is the description
        assert result['zone_id'] in ['z_a', 'z_b', 'z_c', 'z_d', 'z_e', 'z_f']
    
    def test_rate_per_kg_calculation(self, shadowfax_surface_05kg):
        """Test: Verify rate per kg is calculated"""
        rate_dict = shadowfax_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=504273,
            dest_pincode=400075,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert 'rate_per_kg' in result['breakdown']
        assert result['breakdown']['rate_per_kg'] > 0
    
    def test_profit_margin_15_percent(self, shadowfax_surface_05kg):
        """Test: Verify 15% profit margin is applied"""
        rate_dict = shadowfax_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=504273,
            dest_pincode=400075,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        breakdown = result['breakdown']
        expected_profit = round(breakdown['courier_payable'] * 0.15, 2)
        assert abs(breakdown['profit_margin'] - expected_profit) < 0.01
    
    def test_gst_18_percent(self, shadowfax_surface_05kg):
        """Test: Verify 18% GST is applied"""
        rate_dict = shadowfax_surface_05kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=504273,
            dest_pincode=400075,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        breakdown = result['breakdown']
        expected_gst = round(breakdown['amount_before_tax'] * 0.18, 2)
        assert abs(breakdown['gst_amount'] - expected_gst) < 0.01
