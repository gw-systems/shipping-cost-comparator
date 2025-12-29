import pandas as pd
import json
import os

# 1. Configuration & Dependency Loading
def load_config(filename):
    """Loads JSON configuration from the app/config directory."""
    path = os.path.join(os.path.dirname(__file__), "config", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file missing: {path}")
    with open(path, "r") as f:
        return json.load(f)

# Load global configs once at startup
METRO_CITIES = load_config("metro_cities.json")
ZONE_E_STATES = load_config("special_states.json")

# 2. Optimized Database Loading
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "pincode_master.csv")

def initialize_pincode_db():
    """Loads CSV into a dictionary for O(1) lookup performance."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Pincode database missing at {DATA_PATH}")
    
    # Read only necessary columns to save memory
    temp_df = pd.read_csv(DATA_PATH, usecols=['pincode', 'office', 'state', 'district'])
    temp_df.columns = temp_df.columns.str.strip()
    
    # Convert to dictionary: {504273: {'office': '...', 'state': '...', 'district': '...'}, ...}
    return temp_df.set_index('pincode').to_dict('index')

# Global Lookup Table
PINCODE_LOOKUP = initialize_pincode_db()

# 3. Helper Functions
def normalize_state(state: str) -> str:
    """Standardizes state names for reliable matching."""
    return str(state).lower().replace("&", "and").strip()

def is_metro(loc: dict) -> bool:
    """Checks if a location is a metro using optimized keyword matching."""
    city = loc['city'].lower()
    district = loc['district'].lower()
    # Pre-check is faster than full iteration if lists are large
    return any(m in city or m in district for m in METRO_CITIES)

def get_location_details(pincode: int):
    """Lightning-fast dictionary lookup."""
    data = PINCODE_LOOKUP.get(pincode)
    if data:
        return {
            "city": str(data['office']).lower().strip(),
            "state": normalize_state(data['state']),
            "district": str(data['district']).lower().strip()
        }
    return None

# 4. Main Zone Assignment Logic
def get_zone_column(source_pincode: int, dest_pincode: int):
    """
    Assigns shipping zones based on priority hierarchy.
    Returns: (zone_id, human_readable_label)
    """
    s_loc = get_location_details(source_pincode)
    d_loc = get_location_details(dest_pincode)

    if not s_loc or not d_loc:
        return "z_d", "Zone D (National - Pincode Not Found)"

    # PRIORITY 1: Zone E (Special Override - NE/J&K)
    if s_loc['state'] in ZONE_E_STATES or d_loc['state'] in ZONE_E_STATES:
        return "z_f", "Zone E (Special/NE/J&K)"

    # PRIORITY 2: Zone A (Local - Same Office)
    if s_loc['city'] == d_loc['city']:
        return "z_a", "Zone A (Local)"

    # PRIORITY 3: Zone B (Regional - Same State)
    if s_loc['state'] == d_loc['state']:
        return "z_b", "Zone B (Regional/Same State)"

    # PRIORITY 4: Zone C (Metro to Metro)
    if is_metro(s_loc) and is_metro(d_loc):
        return "z_c", "Zone C (Metro to Metro)"

    # PRIORITY 5: Zone D (National - Default)
    return "z_d", "Zone D (National/Rest of India)"