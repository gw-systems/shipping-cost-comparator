from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import RateRequest
from .engine import calculate_cost
from .zones import get_zone_column
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins (local file or website)
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "rate_cards.json")

def load_rates():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.post("/compare-rates")
def compare_rates(request: RateRequest):
    # Unpack both the key and the human-readable label
    zone_key, zone_label = get_zone_column(request.source_pincode, request.dest_pincode)
    
    rates = load_rates()
    results = []

    for carrier in rates:
        # Filtering by mode
        req_mode = request.mode.lower()
        car_mode = carrier.get("mode", "Surface").lower()
        if req_mode != "both" and car_mode != req_mode:
            continue

        try:
            res = calculate_cost(
                weight=request.weight,
                zone_key=zone_key,
                carrier_data=carrier,
                is_cod=request.is_cod,
                order_value=request.order_value
            )
            
            # ADD THE ZONE LABEL HERE
            res["applied_zone"] = zone_label
            res["mode"] = carrier.get("mode", "Surface")
            
            results.append(res)
        except Exception as e:
            print(f"Error: {e}")
            continue

    return sorted(results, key=lambda x: x["total_cost"])