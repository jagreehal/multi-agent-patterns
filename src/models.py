"""
Shared models used across different multi-agent pattern examples.
This ensures consistency in data structures and validation.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class FlightDetails(BaseModel):
    """Details of a flight."""

    flight_number: str
    price: float
    origin: str = Field(description="Three-letter airport code")
    destination: str = Field(description="Three-letter airport code")
    departure_date: date
    arrival_date: date
    duration_hours: float


class SeatPreference(BaseModel):
    """Seat preference details."""

    row: int = Field(ge=1, le=30)
    seat: str = Field(description="Seat letter (A-F)")
    is_window: bool
    is_extra_legroom: bool


class PaymentDetails(BaseModel):
    """Payment processing details."""

    total_amount: float
    payment_method: str
    confirmation_number: str
    status: str = Field(description="Status of the payment: 'success' or 'failed'")
    failure_reason: Optional[str] = None


class TravelPlan(BaseModel):
    """Complete travel plan including flights and recommendations."""

    outbound_flight: FlightDetails
    return_flight: Optional[FlightDetails] = None
    hotel_recommendations: List[str]
    activity_suggestions: List[str]
    total_budget: float


class BookingFailed(BaseModel):
    """Used when booking cannot be completed."""

    reason: str
