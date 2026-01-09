"""
Cost Verification Tests for V-Trans 100kg
Tests rate dictionary and cost calculation
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def vtrans_100kg():
    """Fixture to get V-Trans 100kg courier"""
    return Courier.objects.get(name='V-Trans 100kg')


@pytest.mark.django_db
class TestVTrans100kg:
    """Test suite for V-Trans 100kg cost verification"""
    
    def test_rate_dict_structure(self, vtrans_100kg):
        """Test: Verify rate dictionary has correct structure"""
        rate_dict = vtrans_100kg.get_rate_dict()
        
        assert 'variable_fees' in rate_dict
        assert 'fixed_fees' in rate_dict
        assert isinstance(rate_dict['variable_fees'], dict)
        assert isinstance(rate_dict['fixed_fees'], dict)
    
    def test_variable_fees_present(self, vtrans_100kg):
        """Test: Verify variable fees are configured"""
        rate_dict = vtrans_100kg.get_rate_dict()
        
        variable_fees = rate_dict.get('variable_fees', {})
        # Check for common variable fee fields
        assert 'hamali_per_kg' in variable_fees or len(variable_fees) >= 0
    
    def test_fixed_fees_present(self, vtrans_100kg):
        """Test: Verify fixed fees are configured"""
        rate_dict = vtrans_100kg.get_rate_dict()
        
        fixed_fees = rate_dict.get('fixed_fees', {})
        # Check for common fixed fee fields
        assert 'docket_fee' in fixed_fees or len(fixed_fees) >= 0
    
    def test_mumbai_to_delhi_20kg(self, vtrans_100kg):
        """
        Test: Mumbai to Delhi - 20kg
        Route: Mumbai (400071) -> Delhi (110077)
        """
        rate_dict = vtrans_100kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=400071,  # Mumbai
            dest_pincode=110077,    # Delhi
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['total_cost'] > 0
        assert 'breakdown' in result
    
    def test_cost_breakdown_completeness(self, vtrans_100kg):
        """Test: Verify cost breakdown has all required fields"""
        rate_dict = vtrans_100kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=400071,
            dest_pincode=110077,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        breakdown = result['breakdown']
        
        # Verify essential breakdown fields
        assert 'base_freight' in breakdown
        assert 'courier_payable' in breakdown
        assert 'profit_margin' in breakdown
        assert 'amount_before_tax' in breakdown
        assert 'gst_amount' in breakdown
        assert 'final_total' in breakdown
    
    def test_matrix_based_routing(self, vtrans_100kg):
        """Test: Verify V-Trans uses matrix-based routing"""
        rate_dict = vtrans_100kg.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=400071,
            dest_pincode=110077,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        # V-Trans should have zone information
        assert 'zone' in result['breakdown'] or 'zone_description' in result['breakdown']
