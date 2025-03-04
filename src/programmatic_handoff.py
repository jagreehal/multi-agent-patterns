"""
This example demonstrates the Programmatic Handoff Pattern for flight booking:

1. Each step (search, seat selection, payment) is handled by a specialized agent
2. Control flow is managed programmatically rather than through agent delegation
3. Clear separation between agent responsibilities
4. Explicit error handling and state management
5. Usage tracking across agent handoffs
"""

import asyncio
from datetime import date
from typing import List, Optional, Union

import dotenv
import logfire
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai.usage import Usage, UsageLimits

from config import ACTIVE_MODEL
from models import BookingFailed, FlightDetails, PaymentDetails, SeatPreference

dotenv.load_dotenv()
logfire.configure(send_to_logfire="if-token-present")

# Flight search agent
flight_search_agent: Agent[None, List[FlightDetails]] = Agent(
    ACTIVE_MODEL,
    result_type=List[FlightDetails],
    system_prompt="Find available flights matching the search criteria.",
)

# Seat selection agent
seat_selection_agent: Agent[None, SeatPreference] = Agent(
    ACTIVE_MODEL,
    result_type=SeatPreference,
    system_prompt="""Help users select their seat based on their preferences.
    - Rows 1, 14, and 20 have extra legroom
    - Seats A and F are window seats
    """,
)


# For payment agent, we need to create a custom result type that can handle both success and failure
class PaymentResult(BaseModel):
    """Combined payment result type."""

    success: bool
    data: Union[PaymentDetails, BookingFailed]


# Payment processing agent
payment_agent: Agent[None, PaymentResult] = Agent(
    ACTIVE_MODEL,
    result_type=PaymentResult,
    system_prompt="Process payment and generate booking confirmation.",
)

# Mock flight database
MOCK_FLIGHTS = [
    FlightDetails(
        flight_number="AA123",
        price=299.99,
        origin="SFO",
        destination="JFK",
        departure_date=date(2024, 5, 1),
        arrival_date=date(2024, 5, 1),
        duration_hours=5.5,
    )
]


async def search_flights(usage: Usage, origin: str, destination: str, travel_date: date) -> Optional[FlightDetails]:
    """Step 1: Search for flights."""
    result = await flight_search_agent.run(f"Find flights from {origin} to {destination} on {travel_date}", usage=usage)

    if not result.data:
        print("No flights found")
        return None

    # Return the first available flight for simplicity
    return result.data[0]


async def select_seat(usage: Usage, preferences: str) -> Optional[SeatPreference]:
    """Step 2: Select seat based on user preferences."""
    message_history: List[ModelMessage] = []

    while True:
        result = await seat_selection_agent.run(preferences, usage=usage, message_history=message_history)

        # Validate seat selection
        seat = result.data
        if 1 <= seat.row <= 30 and seat.seat in "ABCDEF":
            return seat

        message_history = result.all_messages(result_tool_return_content="Invalid seat selection, please try again.")


async def process_payment(
    usage: Usage, flight: FlightDetails, seat: SeatPreference, payment_info: str
) -> Union[PaymentDetails, BookingFailed]:
    """Step 3: Process payment and confirm booking."""
    result = await payment_agent.run(
        f"""Process payment for:
        Flight: {flight.flight_number}
        Price: ${flight.price}
        Seat: {seat.row}{seat.seat}

        Payment info: {payment_info}
        """,
        usage=usage,
    )
    payment_result = result.data
    return payment_result.data


async def main() -> None:
    # Initialize usage tracking
    usage = Usage()
    UsageLimits(request_limit=15)

    # Step 1: Search for flights
    print("\nSearching for flights...")
    flight = await search_flights(usage=usage, origin="SFO", destination="JFK", travel_date=date(2024, 5, 1))

    if not flight:
        return

    print(f"Found flight {flight.flight_number} for ${flight.price}")

    # Step 2: Select seat
    print("\nSelecting seat...")
    seat = await select_seat(usage=usage, preferences="I'd like a window seat with extra legroom if possible")

    if not seat:
        return

    print(f"Selected seat {seat.row}{seat.seat}")

    # Step 3: Process payment
    print("\nProcessing payment...")
    payment_result = await process_payment(
        usage=usage, flight=flight, seat=seat, payment_info="Credit card ending in 1234"
    )

    if isinstance(payment_result, BookingFailed):
        print(f"Booking failed: {payment_result.reason}")
        return

    print("\nBooking confirmed!")
    print(f"Confirmation number: {payment_result.confirmation_number}")
    print(f"Total amount paid: ${payment_result.total_amount}")
    print(f"Payment method: {payment_result.payment_method}")


if __name__ == "__main__":
    asyncio.run(main())
