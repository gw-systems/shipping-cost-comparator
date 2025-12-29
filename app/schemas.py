from pydantic import BaseModel, Field, field_validator
from typing import Literal

class RateRequest(BaseModel):
    source_pincode: int = Field(..., description="6-digit origin pincode")
    dest_pincode: int = Field(..., description="6-digit destination pincode")
    weight: float = Field(..., gt=0, lt=1000, description="Weight in kg")
    is_cod: bool = False
    order_value: float = Field(0.0, ge=0)
    # Using Literal ensures ONLY these three strings are accepted
    mode: Literal["Both", "Surface", "Air"] = "Both"

    @field_validator('source_pincode', 'dest_pincode')
    @classmethod
    def validate_pincodes(cls, v: int) -> int:
        if not (100000 <= v <= 999999):
            raise ValueError('Pincode must be exactly 6 digits.')
        return v

# --- NEW: Breakdown Nested Schema ---
class CostBreakdown(BaseModel):
    base_forward: float
    additional_weight: float
    cod: float
    gst: float
    applied_gst_rate: str

# --- Updated: To match your engine.py output exactly ---
class CarrierResponse(BaseModel):
    carrier: str
    total_cost: float
    breakdown: CostBreakdown
    applied_zone: str  # Important for user transparency
    mode: str