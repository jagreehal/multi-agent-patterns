import asyncio
from datetime import date
from typing import List, Optional

import dotenv
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits

from config import ACTIVE_MODEL
from models import FlightDetails

dotenv.load_dotenv()
logfire.configure(send_to_logfire="if-token-present")


class FlightSearchResult(BaseModel):
    """Result of a flight search."""

    found_flights: List[FlightDetails]
    best_flight: Optional[FlightDetails] = None
    explanation: str = Field(description="Explanation of why this flight was chosen as best")


# Create the flight search agent
flight_search_agent: Agent[None, FlightSearchResult] = Agent(
    ACTIVE_MODEL,
    result_type=FlightSearchResult,
    system_prompt="""You are a flight search expert. Your job is to:
1. Search available flights using the search_flights tool
2. Analyze the results to find the best option based on price and duration
3. Provide a clear explanation of why you chose that flight
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
]


@flight_search_agent.tool
async def search_flights(ctx: RunContext[None], origin: str, destination: str, date: date) -> List[FlightDetails]:
    """Search for available flights.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        date: Desired departure date
    """
    # In reality, this would call an actual flight search API
    return [f for f in MOCK_FLIGHTS if f.origin == origin and f.destination == destination and f.departure_date == date]


async def main() -> None:
    # Set usage limits
    usage_limits = UsageLimits(request_limit=5)

    # Example search
    result = await flight_search_agent.run(
        "Find me the best flight from SFO to JFK on May 1st, 2024", usage_limits=usage_limits
    )

    print("\nSearch Results:")
    print(f"Found {len(result.data.found_flights)} flights")
    if result.data.best_flight:
        print("\nBest Flight:")
        print(f"Flight: {result.data.best_flight.flight_number}")
        print(f"Price: ${result.data.best_flight.price}")
        print(f"Duration: {result.data.best_flight.duration_hours} hours")
        print(f"\nExplanation: {result.data.explanation}")


if __name__ == "__main__":
    asyncio.run(main())
