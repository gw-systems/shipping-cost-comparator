"""
Cost Verification Tests for Shadowfax
Tests cost calculation and breakdown
"""

import pytest
from courier.engine import calculate_cost
from courier.models import Courier


@pytest.fixture
def shadowfax_courier():
    """Fixture to get any Shadowfax courier"""
    return Courier.objects.filter(name__icontains='shadow').first()


@pytest.mark.django_db
class TestShadowfaxCostVerification:
    """Test suite for Shadowfax cost verification"""
    
    def test_courier_exists(self, shadowfax_courier):
        """Test: Verify Shadowfax courier exists in database"""
        assert shadowfax_courier is not None
        assert 'shadow' in shadowfax_courier.name.lower()
    
    def test_mumbai_to_delhi_20kg(self, shadowfax_courier):
        """
        Test: Mumbai to Delhi - 20kg
        Route: Mumbai (400071) -> Delhi (110077)
        """
        rate_dict = shadowfax_courier.get_rate_dict()
        
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
    
    def test_cost_breakdown_completeness(self, shadowfax_courier):
        """Test: Verify all cost breakdown components are present"""
        rate_dict = shadowfax_courier.get_rate_dict()
        
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
        
        # Verify all expected fields are present
        assert 'base_freight' in breakdown
        assert 'fuel_surcharge' in breakdown
        assert 'hamali_charge' in breakdown
        assert 'docket_fee' in breakdown
        assert 'courier_payable' in breakdown
        assert 'profit_margin' in breakdown
        assert 'amount_before_tax' in breakdown
        assert 'gst_amount' in breakdown
        assert 'zone' in breakdown
        assert 'rate_per_kg' in breakdown
    
    def test_zone_assignment(self, shadowfax_courier):
        """Test: Verify zone is correctly assigned"""
        rate_dict = shadowfax_courier.get_rate_dict()
        
        result = calculate_cost(
            weight=20,
            source_pincode=400071,
            dest_pincode=110077,
            carrier_data=rate_dict,
            is_cod=False,
            order_value=0
        )
        
        assert result['serviceable'] == True
        assert result['breakdown']['zone'] is not None
        assert result['breakdown']['rate_per_kg'] > 0
