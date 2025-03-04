import asyncio
from datetime import date
from typing import List, Optional

import dotenv
import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import UsageLimits
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import ACTIVE_MODEL
from models import FlightDetails

dotenv.load_dotenv()
logfire.configure(send_to_logfire="if-token-present")
console = Console()


class FlightSearchResult(BaseModel):
    """Result of a flight search."""

    found_flights: List[FlightDetails]
    best_flight: Optional[FlightDetails] = None
    explanation: str = Field(description="Explanation of why this flight was chosen as best")


# Create the flight search agent
flight_search_agent: Agent[None, FlightSearchResult] = Agent(
    ACTIVE_MODEL,
    result_type=FlightSearchResult,
    system_prompt="""You are a flight search expert. For every query, you must:
1. FIRST use the search_flights tool to find available flights
2. Then analyze the results to find the best option based on the user's preferences
3. Finally, provide a clear explanation of why you chose that flight

When using search_flights:
- Extract the date from the user's query (e.g., "May 1st, 2024")
- Use airport codes (e.g., SFO, JFK)

When choosing the best flight, consider:
- Price vs duration tradeoff
- Time of day preferences (if specified)
- Airline preferences (if specified)
- Any other relevant factors

Remember: You MUST use search_flights first before making any recommendations.
""",
)

# Mock flight database with more variety
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
    FlightDetails(
        flight_number="DL789",
        price=275.50,
        origin="SFO",
        destination="JFK",
        departure_date=date(2024, 5, 1),
        arrival_date=date(2024, 5, 1),
        duration_hours=6.5,
    ),
    FlightDetails(
        flight_number="B6012",
        price=225.00,
        origin="SFO",
        destination="JFK",
        departure_date=date(2024, 5, 1),
        arrival_date=date(2024, 5, 1),
        duration_hours=7.0,
    ),
]


@flight_search_agent.tool
async def search_flights(
    ctx: RunContext[None], origin: str, destination: str, travel_date: date
) -> List[FlightDetails]:
    """Search for available flights.

    Args:
        origin: Origin airport code
        destination: Destination airport code
        travel_date: Desired travel date
    """
    # In reality, this would call an actual flight search API
    return [
        f
        for f in MOCK_FLIGHTS
        if f.origin == origin and f.destination == destination and f.departure_date == travel_date
    ]


def display_flights(flights: List[FlightDetails]) -> None:
    """Display flights in a pretty table format."""
    table = Table(title="Available Flights")
    table.add_column("Flight", style="cyan")
    table.add_column("Price", style="green")
    table.add_column("Duration", style="magenta")

    for flight in flights:
        table.add_row(flight.flight_number, f"${flight.price:.2f}", f"{flight.duration_hours:.1f}h")

    console.print(table)


async def main() -> None:
    # Set usage limits
    usage_limits = UsageLimits(request_limit=5)

    # Example searches with different preferences
    searches = [
        "Find me the best flight from SFO to JFK on May 1st, 2024",
        "I need the cheapest flight from SFO to JFK on May 1st, 2024",
        "What's the fastest flight from SFO to JFK on May 1st, 2024?",
    ]

    for search in searches:
        console.print(Panel(f"[bold blue]Search Query:[/] {search}"))

        result = await flight_search_agent.run(search, usage_limits=usage_limits)

        console.print("\n[bold]Available Flights:[/]")
        display_flights(result.data.found_flights)

        if result.data.best_flight:
            console.print("\n[bold green]Best Flight Recommendation:[/]")
            console.print(f"Flight: {result.data.best_flight.flight_number}")
            console.print(f"Price: ${result.data.best_flight.price:.2f}")
            console.print(f"Duration: {result.data.best_flight.duration_hours:.1f} hours")
            console.print(f"\n[bold]Explanation:[/] {result.data.explanation}")

        console.print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
