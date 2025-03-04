"""
This example demonstrates the Delegation Pattern where a high-level travel planner agent
delegates specific tasks to specialized agents:

1. Travel Planner (Controller) - Coordinates the overall travel planning
2. Flight Search (Delegate) - Specialized in finding flights
3. Each agent has a focused responsibility and clear communication protocol
"""

import asyncio
from datetime import date
from typing import List, Optional

import dotenv
import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits

from config import ACTIVE_MODEL
from models import FlightDetails, TravelPlan

dotenv.load_dotenv()
logfire.configure(send_to_logfire="if-token-present")

# Flight search agent (delegate)
flight_search_agent: Agent[None, List[FlightDetails]] = Agent(
    ACTIVE_MODEL,
    result_type=List[FlightDetails],
    system_prompt="You are a flight search specialist. Find the best flights matching the given criteria.",
)

# Travel planner agent (controller)
travel_planner_agent: Agent[None, TravelPlan] = Agent(
    ACTIVE_MODEL,
    result_type=TravelPlan,
    system_prompt="""You are a travel planning expert. Your job is to:
1. Use the flight_search tool to find suitable flights
2. Suggest hotels and activities at the destination
3. Calculate total budget including flights and estimated other expenses
""",
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
    ),
    FlightDetails(
        flight_number="UA456",
        price=349.99,
        origin="SFO",
        destination="JFK",
        departure_date=date(2024, 5, 1),
        arrival_date=date(2024, 5, 1),
        duration_hours=5.0,
    ),
    # Return flights
    FlightDetails(
        flight_number="AA124",
        price=289.99,
        origin="JFK",
        destination="SFO",
        departure_date=date(2024, 5, 5),
        arrival_date=date(2024, 5, 5),
        duration_hours=6.0,
    ),
]


@flight_search_agent.tool
async def search_flights(ctx: RunContext[None], origin: str, destination: str, date: date) -> List[FlightDetails]:
    """Search for available flights."""
    return [f for f in MOCK_FLIGHTS if f.origin == origin and f.destination == destination and f.departure_date == date]


@travel_planner_agent.tool
async def find_flights(
    ctx: RunContext[None], origin: str, destination: str, departure_date: date, return_date: Optional[date] = None
) -> List[FlightDetails]:
    """Find flights using the specialized flight search agent."""
    # Delegate flight search to the specialized agent
    outbound_result = await flight_search_agent.run(
        f"Find flights from {origin} to {destination} on {departure_date}",
        usage=ctx.usage,  # Pass usage context to track total usage
    )

    flights = outbound_result.data

    if return_date:
        return_result = await flight_search_agent.run(
            f"Find flights from {destination} to {origin} on {return_date}", usage=ctx.usage
        )
        flights.extend(return_result.data)

    return flights


async def main() -> None:
    # Set usage limits for the entire operation
    usage_limits = UsageLimits(request_limit=10)

    # Example travel planning request
    result = await travel_planner_agent.run(
        """Plan a trip from SFO to New York (JFK):
        - Departing May 1st, 2024
        - Returning May 5th, 2024
        - Include hotel and activity suggestions
        """,
        usage_limits=usage_limits,
    )

    print("\nTravel Plan:")
    print(f"\nOutbound Flight: {result.data.outbound_flight.flight_number}")
    print(f"Price: ${result.data.outbound_flight.price}")

    if result.data.return_flight:
        print(f"\nReturn Flight: {result.data.return_flight.flight_number}")
        print(f"Price: ${result.data.return_flight.price}")

    print("\nHotel Recommendations:")
    for hotel in result.data.hotel_recommendations:
        print(f"- {hotel}")

    print("\nSuggested Activities:")
    for activity in result.data.activity_suggestions:
        print(f"- {activity}")

    print(f"\nEstimated Total Budget: ${result.data.total_budget:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
