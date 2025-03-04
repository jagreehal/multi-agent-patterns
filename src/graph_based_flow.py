"""
This example demonstrates the Graph-Based Flow Pattern for a flight booking system:

1. Uses a directed graph to model the booking workflow
2. Each node (SearchFlights, SelectSeat, ProcessPayment) is an independent agent
3. State is maintained and passed between nodes
4. Flow control is determined by agent outcomes
5. Provides clear visualization of the process flow
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Union, cast

import dotenv
import logfire
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from config import ACTIVE_MODEL
from models import BookingFailed, FlightDetails, PaymentDetails, SeatPreference

dotenv.load_dotenv()
logfire.configure(send_to_logfire="if-token-present")

# Create agents with proper model name
flight_search_agent: Agent[None, List[FlightDetails]] = Agent(
    ACTIVE_MODEL,
    result_type=List[FlightDetails],
    system_prompt="Find available flights matching the search criteria.",
)

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


@dataclass
class BookingState:
    """State maintained throughout the booking process."""

    origin: str
    destination: str
    travel_date: date
    selected_flight: Optional[FlightDetails] = None
    selected_seat: Optional[SeatPreference] = None
    payment_info: Optional[str] = None
    booking_confirmed: bool = False
    agent_messages: Dict[str, List[ModelMessage]] = field(default_factory=dict)


@dataclass
class SearchFlights(BaseNode[BookingState]):
    """Search for available flights."""

    docstring_notes = True

    async def run(self, ctx: GraphRunContext[BookingState]) -> BaseNode[BookingState] | End[None]:
        if "flight_search" not in ctx.state.agent_messages:
            ctx.state.agent_messages["flight_search"] = []

        result = await flight_search_agent.run(
            f"Find flights from {ctx.state.origin} to {ctx.state.destination} on {ctx.state.travel_date}",
            message_history=ctx.state.agent_messages["flight_search"],
        )

        ctx.state.agent_messages["flight_search"].extend(result.all_messages())

        if not result.data:
            print("No flights found")
            return End(data=None)

        ctx.state.selected_flight = result.data[0]
        return SelectSeat()


@dataclass
class SelectSeat(BaseNode[BookingState]):
    """Select seat preferences for the flight."""

    docstring_notes = True

    async def run(self, ctx: GraphRunContext[BookingState]) -> BaseNode[BookingState]:
        if "seat_selection" not in ctx.state.agent_messages:
            ctx.state.agent_messages["seat_selection"] = []

        result = await seat_selection_agent.run(
            "I'd like a window seat with extra legroom if possible",
            message_history=ctx.state.agent_messages["seat_selection"],
        )

        ctx.state.agent_messages["seat_selection"].extend(result.all_messages())
        ctx.state.selected_seat = result.data
        return ProcessPayment()


@dataclass
class ProcessPayment(BaseNode[BookingState]):
    """Process payment for the flight booking."""

    docstring_notes = True

    async def run(self, ctx: GraphRunContext[BookingState]) -> BaseNode[BookingState] | End[None]:
        if "payment" not in ctx.state.agent_messages:
            ctx.state.agent_messages["payment"] = []

        assert ctx.state.selected_flight is not None
        assert ctx.state.selected_seat is not None

        result = await payment_agent.run(
            f"""Process payment for:
            Flight: {ctx.state.selected_flight.flight_number}
            Price: ${ctx.state.selected_flight.price}
            Seat: {ctx.state.selected_seat.row}{ctx.state.selected_seat.seat}

            Payment info: Credit card ending in 1234
            """,
            message_history=ctx.state.agent_messages["payment"],
        )

        ctx.state.agent_messages["payment"].extend(result.all_messages())
        payment_result = result.data

        if not payment_result.success:
            failed_payment = cast(BookingFailed, payment_result.data)
            print(f"Booking failed: {failed_payment.reason}")
            return SearchFlights()

        successful_payment = cast(PaymentDetails, payment_result.data)
        print("\nBooking confirmed!")
        print(f"Confirmation number: {successful_payment.confirmation_number}")
        print(f"Total amount paid: ${successful_payment.total_amount}")
        print(f"Payment method: {successful_payment.payment_method}")

        ctx.state.booking_confirmed = True
        return End(data=None)


# Create the booking graph with proper initialization
booking_graph = Graph[BookingState](
    nodes=[SearchFlights, SelectSeat, ProcessPayment],
    name="booking_graph",
)


async def main() -> None:
    # Initialize booking state
    state = BookingState(origin="SFO", destination="JFK", travel_date=date(2024, 5, 1))

    # Run the booking graph
    async with booking_graph.iter(SearchFlights(), state=state) as run:
        node = run.next_node
        while not isinstance(node, End):
            print(f"\nExecuting node: {node.__class__.__name__}")
            node = await run.next(node)

        if state.booking_confirmed:
            print("\nBooking process completed successfully!")
        else:
            print("\nBooking process ended without confirmation")


if __name__ == "__main__":
    asyncio.run(main())
