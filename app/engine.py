import math
import json
import os

# 1. Load Global Settings
def load_settings():
    path = os.path.join(os.path.dirname(__file__), "config", "settings.json")
    with open(path, "r") as f:
        return json.load(f)

SETTINGS = load_settings()

def calculate_cost(weight: float, zone_key: str, carrier_data: dict, is_cod: bool, order_value: float = 0):
    """
    Calculates the total shipping cost based on carrier rates, 
    centralized settings, and COD logic.
    """
    
    # Use slab from settings (typically 0.5)
    slab = SETTINGS.get("DEFAULT_WEIGHT_SLAB", 0.5)
    
    # 1. Base Forward Charge (for first slab)
    base_rate = carrier_data["forward_rates"][zone_key]
    
    # 2. Additional weight increments
    extra_weight_cost = 0
    if weight > slab:
        extra_weight = weight - slab
        # Every 'slab' kg or part thereof is billed as one additional unit
        num_units = math.ceil(extra_weight / slab)
        extra_weight_cost = num_units * carrier_data["additional_rates"][zone_key]
    
    subtotal = base_rate + extra_weight_cost
    
    # 3. COD Logic (Higher of Fixed vs Percentage)
    cod_fee = 0
    if is_cod:
        fee_from_percent = order_value * carrier_data.get("cod_percent", 0)
        cod_fee = max(carrier_data.get("cod_fixed", 0), fee_from_percent)
    
    # 4. Total and GST (Pulled from settings.json)
    gst_rate = SETTINGS.get("GST_RATE", 0.18)
    
    total_before_gst = subtotal + cod_fee
    gst_amount = total_before_gst * gst_rate
    final_total = total_before_gst + gst_amount
    
    return {
        "carrier": carrier_data["carrier_name"],
        "total_cost": round(final_total, 2),
        "breakdown": {
            "base_forward": round(base_rate, 2),
            "additional_weight": round(extra_weight_cost, 2),
            "cod": round(cod_fee, 2),
            "gst": round(gst_amount, 2),
            "applied_gst_rate": f"{int(gst_rate * 100)}%"
        }
    }