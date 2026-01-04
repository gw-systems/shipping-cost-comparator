"""
Tests for zone resolution logic
Refactored for Multi-Carrier Logic
"""

import pytest
from courier.zones import (
    get_zone,
    get_location_details,
    is_metro,
    normalize_name,
    PINCODE_LOOKUP,
)

# Mock Carrier Configs for different models
CARRIER_CITY = {
    "routing_logic": {
        "is_city_specific": True,
        "city_rates": {"test city": 50, "mumbai": 100}
    }
}

CARRIER_MATRIX = {
    "zone_mapping": {
        "maharashtra": "MH",
        "delhi": "DL"
    },
    "routing_logic": {
        "is_city_specific": False
    }
}

CARRIER_STANDARD = {
    "routing_logic": {
        "is_city_specific": False
    }
}

class TestNameNormalization:
    """Tests for normalize_name function"""
    
    def test_normalize_basic(self):
        # "gujarat" is the standard key in alias_map
        assert normalize_name("Gujarat", "state") == "gujarat" 
        assert normalize_name("Gujrat", "state") == "gujarat"
        assert normalize_name("MAHARASHTRA", "state") == "maharashtra" 
        
    def test_normalize_city(self):
        # "ahmedabad" is the standard key
        assert normalize_name("Ahmedabad", "city") == "ahmedabad"
        assert normalize_name("Vapi Ahmedabad", "city") == "ahmedabad" 

class TestGetZone:
    """Tests for Unified get_zone logic"""

    def test_logic_city_specific_match(self):
        # Mumbai (400001) -> Mumbai (Match) - Technically intra-city but simulating city match
        # Need a pincode that maps to "test city" or use real data. 
        # Using Mumbai 400001.
        
        # We need to make sure 400001 resolves to "mumbai" in get_location_details
        zone_id, desc, logic = get_zone(400001, 400001, CARRIER_CITY)
        assert logic == "city_specific"
        assert zone_id == "mumbai"

    def test_logic_matrix_match(self):
        # Mumbai (MH) -> Delhi (DL)
        # 400001 (MH) -> 110001 (DL)
        zone_id, desc, logic = get_zone(400001, 110001, CARRIER_MATRIX)
        assert logic == "matrix"
        assert zone_id == ("MH", "DL")
        
    def test_logic_standard_metro(self):
        # Mumbai -> Delhi (Metro-Metro) -> Zone A
        zone_id, desc, logic = get_zone(400001, 110001, CARRIER_STANDARD)
        assert logic == "standard"
        assert zone_id == "z_a"

    def test_logic_standard_northeast(self):
        # Mumbai -> Zone E (Itanagar 791111)
        zone_id, desc, logic = get_zone(400001, 791111, CARRIER_STANDARD)
        assert logic == "standard"
        assert zone_id == "z_f" # code uses z_f for zone E states logic
