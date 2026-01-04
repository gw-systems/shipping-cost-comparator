import json
import os
import engine
import zones

# Load Master Card for Testing
def load_master_card():
    path = os.path.join(os.path.dirname(__file__), "data", "master_card.json")
    with open(path, "r") as f:
        return json.load(f)

CARRIERS = load_master_card()
ACPL = next(c for c in CARRIERS if "ACPL" in c["carrier_name"])
VTRANS = next(c for c in CARRIERS if "V-Trans" in c["carrier_name"])
SHADOWFAX = next(c for c in CARRIERS if "Shadowfax" in c["carrier_name"])

# Mock Pincodes (Ensure these exist in your CSV or are mocked appropriately)
# If CSV logic fails, zones.py returns error.
PUNE_PIN = 411001
BHOSARI_PIN = 411026
MUMBAI_PIN = 400001
DELHI_PIN = 110001

print("--- STARTING VERIFICATION ---")

# 1. TEST ACPL (City Match)
print("\n[TEST 1] ACPL (City-to-City)")
# Pune -> Bhosari (Should match 'bhosari' in ACPL city_rates)
try:
    res = engine.calculate_cost(55, PUNE_PIN, BHOSARI_PIN, ACPL)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"FAILED: {e}")

# 2. TEST V-TRANS (Matrix)
print("\n[TEST 2] V-TRANS (Zone Matrix)")
# Mumbai (MH1) -> Delhi (N1)
try:
    res = engine.calculate_cost(120, MUMBAI_PIN, DELHI_PIN, VTRANS)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"FAILED: {e}")

# 3. TEST SHADOWFAX (Standard)
print("\n[TEST 3] SHADOWFAX (Standard Zonal)")
# Mumbai -> Delhi (Zone D typically)
try:
    res = engine.calculate_cost(2.5, MUMBAI_PIN, DELHI_PIN, SHADOWFAX)
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"FAILED: {e}")

print("\n--- VERIFICATION COMPLETE ---")
