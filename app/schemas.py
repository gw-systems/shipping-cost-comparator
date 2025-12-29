from pydantic import BaseModel, Field, field_validator
from typing import Annotated

class RateRequest(BaseModel):
    # Use Field for basic constraints (min/max/regex)
    source_pincode: int = Field(..., description="6-digit origin pincode")
    dest_pincode: int = Field(..., description="6-digit destination pincode")
    weight: float = Field(..., gt=0, lt=1000, description="Weight must be between 0 and 1000kg")
    is_cod: bool = False
    order_value: float = Field(0.0, ge=0)
    mode: str = "Both"

    # Pydantic V2 style validator
    @field_validator('source_pincode', 'dest_pincode')
    @classmethod
    def validate_pincodes(cls, v: int) -> int:
        """Ensures the pincode is exactly 6 digits."""
        if not (100000 <= v <= 999999):
            raise ValueError('Pincode must be exactly 6 digits.')
        return v

class CarrierRate(BaseModel):
    carrier_name: str
    mode: str
    base_cost: float
    extra_weight_cost: float
    cod_charges: float
    gst_amount: float
    total_cost: float