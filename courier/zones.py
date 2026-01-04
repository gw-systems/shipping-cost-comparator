import pandas as pd
import json
import os

# --- 1. CONFIGURATION LOADING ---
def load_config(filename):
    path = os.path.join(os.path.dirname(__file__), "config", filename)
    with open(path, "r") as f:
        return json.load(f)

# Load configurations
METRO_CITIES = load_config("metro_cities.json")
ZONE_E_STATES = load_config("special_states.json")
ALIAS_MAP = load_config("alias_map.json")


# --- 2. DATABASE INITIALIZATION ---
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "pincode_master.csv")

def initialize_pincode_lookup():
    if not os.path.exists(DATA_PATH):
        print(f"CRITICAL ERROR: Database not found at {DATA_PATH}")
        return {}

    try:
        temp_df = pd.read_csv(
            DATA_PATH, usecols=["pincode", "office", "state", "district"]
        )
        temp_df.columns = temp_df.columns.str.strip()
        temp_df = temp_df.drop_duplicates(subset=["pincode"], keep="first")
        return temp_df.set_index("pincode").to_dict("index")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to initialize pincode lookup: {e}")
        return {}

PINCODE_LOOKUP = initialize_pincode_lookup()


# --- 3. REFACTORED HELPERS ---
def normalize_name(name: str, type: str = 'state') -> str:
    """
    Normalizes City/State names using alias_map.json.
    Ex: 'Gujarat' -> 'gujrat' (if mapped)
    """
    cleaned = str(name).lower().replace("&", "and").strip()
    
    # Check alias map
    # Handle plural mapping keys
    map_key = type
    if type == "city": map_key = "cities"
    elif type == "state": map_key = "states"
    elif not type.endswith("s"): map_key = type + "s"
    
    section = ALIAS_MAP.get(map_key, {})

    # Invert the map for easier lookup? 
    # Or just iterate. Since list is small, iteration is fine.
    # But for O(1), we should probably index this differently or just loop.
    # For now, simplistic loop check is robust enough for small maps.
    
    # Check if cleaned name matches a key (standard name)
    if cleaned in section:
        return cleaned # It's already standard (or at least a key)
        
    # Check if it's in values
    for standard, aliases in section.items():
        if cleaned == standard or cleaned in aliases:
            return standard
            
    return cleaned

def get_location_details(pincode: int):
    data = PINCODE_LOOKUP.get(pincode)
    if data:
        return {
            "city": normalize_name(data["office"], "city"),
            "state": normalize_name(data["state"], "state"),
            "district": normalize_name(data["district"], "city"), # Approximate district as city type
            "original_city": str(data["office"]).lower().strip(),
            "original_state": str(data["state"]).lower().strip()
        }
    return None

def is_metro(location_dict):
    city = location_dict["city"]
    district = location_dict["district"]
    # METRO_CITIES are assumed to be normalized or lowercase in config
    return any(metro in city or metro in district for metro in METRO_CITIES)


# --- 4. UNIFIED ZONE LOGIC ---
def get_zone(source_pincode: int, dest_pincode: int, carrier_config: dict):
    """
    Determines the Zone Identifier based on Carrier Logic.
    Returns: (zone_id, description, logic_type)
    """
    s_loc = get_location_details(source_pincode)
    d_loc = get_location_details(dest_pincode)

    if not s_loc or not d_loc:
        return None, "Invalid Pincode", None

    routing = carrier_config.get("routing_logic", {})
    
    # --- LOGIC 1: CITY-TO-CITY (e.g., ACPL) ---
    if routing.get("is_city_specific"):
        city_rates = routing.get("city_rates", {})
        # Check Destination City Match
        # Try both normalized and original just in case, but prefer normalized
        dest_city = d_loc["city"]
        
        # Exact match check
        if dest_city in city_rates:
            return dest_city, f"City Match: {dest_city}", "city_specific"
            
        # Fallback 1: Check District (e.g. "Mumbai" matching "MPT SO")
        if d_loc["district"] in city_rates:
            return d_loc["district"], f"City Match: {d_loc['district']}", "city_specific"
            
        # Fallback 2: check original name if normalization was too aggressive
        if d_loc["original_city"] in city_rates:
             return d_loc["original_city"], f"City Match: {d_loc['original_city']}", "city_specific"
             
        return None, "City Not Servicable", "city_specific"

    # --- LOGIC 2: CARRIER SPECIFIC ZONE MATRIX (e.g., V-Trans) ---
    zone_map = carrier_config.get("zone_mapping")
    if zone_map:
        # 1. Map Source State/City to Origin Zone
        # Try State first, then City if needed (not implemented here, assuming State based for V-Trans)
        
        # Check aliases for keys in zone_map would be expensive. 
        # Ideally, zone_map keys should match our normalized names. 
        # Strategy: Iterate zone_map keys and check if s_loc['state'] is an alias/match for that key.
        # However, to be fast, we use our Normalize Name to unify them.
        # Assuming V-Trans keys like "Maharashtra" map to our normalized "maharashtra" (or we update alias map to match V-Trans).
        # BETTER: Use helper to find map key.
        
        def find_mapped_zone(loc_details, mapping):
            # Check State
            state = loc_details["state"]
            # We need to find if 'state' matches a key in 'mapping' considering case-insensitivity
            # mapping keys might be "Maharashtra" (Title Case).
            for key, code in mapping.items():
                if normalize_name(key, "state") == state:
                    return code
            return None

        origin_zone = find_mapped_zone(s_loc, zone_map)
        dest_zone = find_mapped_zone(d_loc, zone_map)

        if origin_zone and dest_zone:
            # We return the tuple (Origin, Dest) to be looked up in matrix by engine
            return (origin_zone, dest_zone), f"Matrix: {origin_zone}->{dest_zone}", "matrix"
            
        return "z_d", "Zone Mapping Failed (Defaulting)", "matrix" # Fallback or Error?

    # --- LOGIC 3: STANDARD ZONAL (Shadowfax/Courier) ---
    # Existing Logic
    if s_loc["state"] in ZONE_E_STATES or d_loc["state"] in ZONE_E_STATES:
         return "z_f", "Zone E (North-East & J&K)", "standard"
    
    if is_metro(s_loc) and is_metro(d_loc):
        return "z_a", "Zone A (Metropolitan)", "standard"
        
    if s_loc["state"] == d_loc["state"]:
        return "z_b", "Zone B (Regional)", "standard"
        
    if s_loc["city"] != d_loc["city"]:
        return "z_c", "Zone C (Intercity)", "standard" # Note: logic check might need tuning vs z_d
        
    return "z_d", "Zone D (Pan-India)", "standard"

# --- 5. LEGACY WRAPPER (For Backward Compatibility) ---
def get_zone_column(source_pincode: int, dest_pincode: int):
    """
    Legacy wrapper for existing views that expect a simple (zone_id, description) tuple.
    Uses 'Standard' logic by default.
    """
    # Dummy config to trigger Standard Zonal Logic
    dummy_config = {
        "routing_logic": {
            "is_city_specific": False
            # No zone_mapping implies standard logic fallback
        }
    }
    
    zone_id, desc, logic = get_zone(source_pincode, dest_pincode, dummy_config)
    return zone_id, desc
