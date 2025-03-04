"""
Shared models used across different multi-agent pattern examples.
This ensures consistency in data structures and validation.

These models represent core entities in a travel booking system, with each model
handling specific aspects like flight details, seat preferences, payments, and
complete travel plans. The models use Pydantic for data validation and serialization.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class FlightDetails(BaseModel):
    """Details of a flight."""

    flight_number: str = Field(description="Unique flight identifier (e.g., 'AA123', 'DL456')")
    price: float = Field(description="Current price of the flight in USD")
    origin: str = Field(description="Three-letter IATA code for departure airport (e.g., 'SFO')")
    destination: str = Field(description="Three-letter IATA code for arrival airport (e.g., 'JFK')")
    departure_date: date = Field(description="Date of flight departure in YYYY-MM-DD format")
    arrival_date: date = Field(description="Date of flight arrival in YYYY-MM-DD format")
    duration_hours: float = Field(description="Total flight duration in hours (e.g., 5.5 for 5 hours 30 minutes)")


class SeatPreference(BaseModel):
    """Seat preference details."""

    row: int = Field(ge=1, le=30, description="Row number in the aircraft (1-30)")
    seat: str = Field(
        description="Seat letter (A-F), where A/F are window seats, B/E are middle seats, and C/D are aisle seats"
    )
    is_window: bool = Field(description="Indicates if this is a window seat preference")
    is_extra_legroom: bool = Field(
        description="Indicates if extra legroom is requested (usually exit rows or bulkhead seats)"
    )


class PaymentDetails(BaseModel):
    """Payment processing details."""

    total_amount: float = Field(description="Total payment amount in USD")
    payment_method: str = Field(description="Payment method used (e.g., 'credit_card', 'paypal', 'bank_transfer')")
    confirmation_number: str = Field(description="Unique payment confirmation identifier")
    status: str = Field(description="Status of the payment: 'success' or 'failed'")
    failure_reason: Optional[str] = Field(None, description="Reason for payment failure if status is 'failed'")


class TravelPlan(BaseModel):
    """Complete travel plan including flights and recommendations."""

    outbound_flight: FlightDetails = Field(description="Details of the outbound flight")
    return_flight: Optional[FlightDetails] = Field(None, description="Details of the return flight (if round-trip)")
    hotel_recommendations: List[str] = Field(description="List of recommended hotels near the destination")
    activity_suggestions: List[str] = Field(
        description="List of suggested activities or attractions at the destination"
    )
    total_budget: float = Field(description="Total budget allocation for the entire trip in USD")


class BookingFailed(BaseModel):
    """Used when booking cannot be completed."""

    reason: str = Field(description="Detailed explanation of why the booking failed")
