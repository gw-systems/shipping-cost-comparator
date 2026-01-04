import math
import json
import os
from courier import zones  # The refactored zones module

# 1. Load Global Settings & Surcharges
def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), "config", filename)
    with open(path, "r") as f:
        return json.load(f)

SETTINGS = load_json("settings.json")
GLOBAL_CHARGES = load_json("charges_config.json")

def calculate_cost(
    weight: float,
    source_pincode: int,
    dest_pincode: int,
    carrier_data: dict,
    is_cod: bool = False,
    order_value: float = 0,
):
    """
    Calculates shipping cost supporting 3 Models:
    1. City-to-City (Per KG)
    2. Zone Matrix (Per KG)
    3. Standard Zonal (Slab Based)
    """
    
    # --- STEP 1: IDENTIFY ZONE ---
    zone_id, zone_desc, logic_type = zones.get_zone(source_pincode, dest_pincode, carrier_data)
    
    if not zone_id:
        return {
            "carrier": carrier_data["carrier_name"],
            "error": zone_desc,
            "servicable": False
        }

    # --- STEP 2: FREIGHT CALCULATION ---
    routing = carrier_data.get("routing_logic", {})
    freight_min = carrier_data.get("min_freight", 0)
    # Use max of actual weight or volumetric? (Not implemented here, assuming 'weight' input is chargeable weight)
    
    freight_cost = 0
    breakdown = {}

    # MODEL A: Per KG Pricing (City-Specific or Matrix)
    if logic_type in ["city_specific", "matrix"]:
        # Lookup Rate
        rate_per_kg = 0
        if logic_type == "city_specific":
            rate_per_kg = routing.get("city_rates", {}).get(zone_id, 0)
        elif logic_type == "matrix":
            origin, dest = zone_id
            rate_per_kg = routing.get("zonal_rates", {}).get(origin, {}).get(dest, 0)
            
        # Calculate
        charged_weight = max(weight, carrier_data.get("min_weight", 0))
        raw_freight = charged_weight * rate_per_kg
        freight_cost = max(raw_freight, freight_min)
        
        breakdown["rate_per_kg"] = rate_per_kg
        breakdown["charged_weight"] = charged_weight
        breakdown["base_freight"] = freight_cost

    # MODEL B: Slab Based Pricing (Standard Zonal)
    elif logic_type == "standard":
        slab = carrier_data.get("min_weight", 0.5) # Default slab 0.5kg
        
        # Backward compatibility: support old format (forward_rates at top level)
        # vs new format (routing_logic.zonal_rates.forward)
        if routing.get("zonal_rates"):
            forward_rates = routing["zonal_rates"].get("forward", {})
            additional_rates = routing["zonal_rates"].get("additional", {})
        else:
            # Old format - rates at top level
            forward_rates = carrier_data.get("forward_rates", {})
            additional_rates = carrier_data.get("additional_rates", {})
        
        base_rate = forward_rates.get(zone_id, 0)
        extra_rate = additional_rates.get(zone_id, 0)
        
        # Calculation
        freight_cost = base_rate
        if weight > slab:
            extra_weight = weight - slab
            # Determine slab steps (assuming 0.5 or equal to min_weight)
            # Typically additional slab is same size as min_weight for couriers, or 0.5
            slab_step = slab 
            units = math.ceil(extra_weight / slab_step)
            extra_cost = units * extra_rate
            freight_cost += extra_cost
            breakdown["extra_weight_charge"] = extra_cost
            
        breakdown["base_slab_rate"] = base_rate
        breakdown["base_freight"] = freight_cost

    # --- STEP 3: SURCHARGES (Carrier Specific) ---
    fixed_fees = carrier_data.get("fixed_fees", {})
    var_fees = carrier_data.get("variable_fees", {})
    
    # 1. Docket/One-time Fees
    docket_fee = fixed_fees.get("docket_fee", 0)
    
    # 2. COD Fees (backward compatible with old format)
    cod_fee = 0
    if is_cod:
        # Try new format first (inside fixed_fees/variable_fees)
        cod_fixed = fixed_fees.get("cod_fixed", 0)
        cod_percent = var_fees.get("cod_percent", 0)
        
        # Fallback to old format (at top level)
        if cod_fixed == 0:
            cod_fixed = carrier_data.get("cod_fixed", 0)
        if cod_percent == 0:
            cod_percent = carrier_data.get("cod_percent", 0)
        
        # Normalize percentage (if > 1, assume it's a percentage like 1.5%)
        if cod_percent > 1: 
            cod_percent = cod_percent / 100
            
        cod_fee = max(cod_fixed, order_value * cod_percent)
    
    # 3. Fuel Surcharge (If dynamic/percent)
    fuel_cost = 0
    # Check global or carrier? 
    # Logic: Global Surcharge layer added on TOP of everything?
    # Or Carrier Fuel Surcharge is part of freight?
    # Usually Carrier Fuel = Base Freight * Fuel %.
    fuel_config = carrier_data.get("fuel_config", {})
    # For now, simplistic implementation using Global Config as requested for "Final Layer"
    # But Carrier might have its own. 
    # Let's use Global Fuel Surcharge from charges_config.json as the requirement says "add a final layer... from separate charges_config"
    
    current_subtotal = freight_cost + docket_fee + cod_fee

    # --- STEP 4: GLOBAL SURCHARGES (Config Layer) ---
    global_surcharges = 0
    global_surcharge_breakdown = {}
    
    # Fixed Global
    for name, amount in GLOBAL_CHARGES.get("fixed_charges", {}).items():
        global_surcharges += amount
        global_surcharge_breakdown[name] = amount
        
    # Percentage Global (on Subtotal)
    for name, percent in GLOBAL_CHARGES.get("percentage_charges", {}).items():
        amt = current_subtotal * percent
        global_surcharges += amt
        global_surcharge_breakdown[name] = amt
        
    total_cost = current_subtotal + global_surcharges
    
    # --- STEP 5: FINAL ASSEMBLY ---
    return {
        "carrier": carrier_data["carrier_name"],
        "zone": zone_desc,
        "total_cost": round(total_cost, 2),
        "breakdown": {
            **breakdown,
            "docket_fee": docket_fee,
            "cod_fee": round(cod_fee, 2),
            "carrier_subtotal": round(current_subtotal, 2),
            "global_surcharges": global_surcharges,
            "surcharge_details": global_surcharge_breakdown
        },
        "servicable": True
    }
