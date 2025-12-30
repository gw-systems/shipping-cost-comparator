from fastapi import FastAPI, HTTPException, APIRouter, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from .schemas import RateRequest
from .engine import calculate_cost
from .zones import get_zone_column
import json
import os
from dotenv import load_dotenv
import shutil

load_dotenv() # Loads the .env file

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# --- 1. GLOBAL PATH CONFIGURATION ---
# Define ONE source of truth for your data file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RATE_CARD_PATH = os.path.join(BASE_DIR, "data", "rate_cards.json")

# --- 2. ADMIN ROUTER ---

async def verify_admin_token(x_admin_token: str = Header(None)):
    """
    Dependency to verify the admin password from the request header.
    """
    if x_admin_token != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Admin Token",
        )
    return x_admin_token

admin_router = APIRouter(
    prefix="/api/admin", 
    tags=["Admin"],
    dependencies=[Depends(verify_admin_token)] # <--- Security added here
)

@admin_router.get("/rates")
async def get_all_rates():
    # This code is now protected!
    with open(RATE_CARD_PATH, "r") as f:
        return json.load(f)

@admin_router.post("/rates/update")
async def update_rates(new_data: list):
    try:
        # Create a COPY for backup rather than moving the file
        if os.path.exists(RATE_CARD_PATH):
            shutil.copy(RATE_CARD_PATH, RATE_CARD_PATH + ".bak")
            
        # Write the new data
        with open(RATE_CARD_PATH, "w") as f:
            json.dump(new_data, f, indent=4)
            
        return {"status": "success", "message": "Rates updated successfully"}
    except Exception as e:
        # If writing fails, we still have the original/backup safe
        raise HTTPException(status_code=500, detail=f"Failed to update rates: {str(e)}")

# --- 3. MAIN APP INITIALIZATION ---
app = FastAPI(title="LogiRate API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the Admin Router so it actually works!
app.include_router(admin_router)

def load_rates():
    if not os.path.exists(RATE_CARD_PATH):
        return []
    with open(RATE_CARD_PATH, "r") as f:
        return json.load(f)

# --- 4. PUBLIC API ROUTES ---
@app.post("/compare-rates")
def compare_rates(request: RateRequest):
    zone_key, zone_label = get_zone_column(request.source_pincode, request.dest_pincode)
    
    rates = load_rates()
    results = []

    for carrier in rates:
        # Check if carrier is active (Industry-Grade Toggle)
        if not carrier.get("active", True):
            continue

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
            
            res["applied_zone"] = zone_label
            res["mode"] = carrier.get("mode", "Surface")
            results.append(res)
        except Exception as e:
            # In production, use a logger here, not print
            print(f"Calculation Error for {carrier.get('carrier_name')}: {e}")
            continue

    return sorted(results, key=lambda x: x["total_cost"])