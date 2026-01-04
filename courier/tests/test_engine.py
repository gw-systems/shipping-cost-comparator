"""
Tests for pricing calculation engine
Refactored for Multi-Carrier Logic (Per KG, Matrix, Slab)
"""

import pytest
from courier.engine import calculate_cost

# --- MOCK DATA ---
# 1. City Model (Per KG)
CARRIER_CITY = {
    "carrier_name": "City Carrier",
    "min_weight": 5,
    "routing_logic": {
        "is_city_specific": True,
        "city_rates": {"mumbai": 10} # 10 per kg locally
    },
    "fixed_fees": {"docket_fee": 50},
    "variable_fees": {"cod_percent": 0},
    "fuel_config": {}
}

# 2. Matrix Model (Per KG) - V-Trans style
CARRIER_MATRIX = {
    "carrier_name": "Matrix Carrier",
    "min_weight": 5,
    "zone_mapping": {"maharashtra": "MH", "delhi": "DL"},
    "routing_logic": {
        "zonal_rates": {
            "MH": {"DL": 20} # 20 per kg MH->DL
        }
    },
    "fixed_fees": {"docket_fee": 50},
    "variable_fees": {},
    "fuel_config": {}
}

# 3. Standard Model (Slab) - Shadowfax style
CARRIER_STANDARD = {
    "carrier_name": "Standard Carrier",
    "min_weight": 0.5,
    "routing_logic": {
        "is_city_specific": False,
        "zonal_rates": {
            "forward": {"z_a": 30, "z_d": 40},
            "additional": {"z_a": 20, "z_d": 30}
        }
    },
    "fixed_fees": {"docket_fee": 20, "cod_fixed": 30},
    "variable_fees": {"cod_percent": 0.02}, # 2%
    "fuel_config": {}
}

# Real Pincodes for Lookup
PUNE = 411001
MUMBAI = 400001
DELHI = 110001


class TestCalculateCost:

    def test_model_city_per_kg(self):
        # Rate 10/kg. Weight 10kg. Cost 100. Docket 50. Global Surcharges extra.
        # Mumbai -> Mumbai (mapped to 'mumbai')
        res = calculate_cost(10, MUMBAI, MUMBAI, CARRIER_CITY, is_cod=False)
        
        assert res["servicable"] is True
        assert res["breakdown"]["rate_per_kg"] == 10
        assert res["breakdown"]["base_freight"] == 100 # 10 * 10
        assert res["breakdown"]["docket_fee"] == 50
        # Check carrier subtotal = 150
        assert res["breakdown"]["carrier_subtotal"] == 150
        # Check total > 150 (due to global surcharges)
        assert res["total_cost"] > 150

    def test_model_matrix_per_kg(self):
        # Rate 20/kg MH->DL. Weight 10kg. Cost 200. Docket 50.
        res = calculate_cost(10, MUMBAI, DELHI, CARRIER_MATRIX, is_cod=False)
        
        assert res["servicable"] is True
        assert res["zone"] == "Matrix: MH->DL"
        assert res["breakdown"]["rate_per_kg"] == 20
        assert res["breakdown"]["base_freight"] == 200
        assert res["breakdown"]["carrier_subtotal"] == 250

    def test_model_standard_slab(self):
        # Mumbai->Delhi (Metro-Metro) -> Zone A ? No, Mumbai(MH)->Delhi(DL) is Zone C or A depending on logic.
        # Check zones.py logic: is_metro(Mum)=True, is_metro(Del)=True -> z_a.
        # Slab 0.5kg. Rate 30. Additional 20.
        # Weight 1.5kg.
        # Base (0.5) = 30.
        # Extra (1.0) = 2 units * 20 = 40.
        # Total Freight = 70.
        # Docket = 20.
        # Subtotal = 90.
        
        res = calculate_cost(1.5, MUMBAI, DELHI, CARRIER_STANDARD, is_cod=False)
        
        assert res["servicable"] is True
        assert res["zone"] == "Zone A (Metropolitan)"
        assert res["breakdown"]["base_slab_rate"] == 30
        assert res["breakdown"]["extra_weight_charge"] == 40
        assert res["breakdown"]["base_freight"] == 70
        assert res["breakdown"]["carrier_subtotal"] == 90
        
    def test_cod_logic(self):
        # Standard carrier COD. Fixed 30. Percent 2%.
        # Order value 5000 * 0.02 = 100. Max(30, 100) = 100.
        
        res = calculate_cost(0.5, MUMBAI, DELHI, CARRIER_STANDARD, is_cod=True, order_value=5000)
        assert res["breakdown"]["cod_fee"] == 100
