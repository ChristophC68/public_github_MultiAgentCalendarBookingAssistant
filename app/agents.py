from pydantic_ai import Agent, RunContext
from app.schemas import CalendarChangeAnalysis, BookingResult
from app.dependencies import AgentDependencies
import os


from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

# Access them securely
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

# gpt-oss:20b 13 GB 
agent = Agent(
    'ollama:gpt-oss:20b',
    deps_type=AgentDependencies,
    output_type=BookingResult, # this is only type checking, no passing of context happens here
    retries=3
)


# 1. Tool for communicating failures back to the user
@agent.tool
async def send_clarification_email(
    ctx: RunContext[AgentDependencies], 
    recipient: str, 
    message: str
) -> str:
    """Sends an email to the user when details are missing or an error occurs."""
    email_body = (
        f"Hi there,\n\n"
        f"I tried processing your calendar booking request, but ran into an issue:\n"
        f"{message}\n\n"
        f"Please update your calendar entry with further instructions (e.g., change dates, "
        f"adjust budget, or change location) so I can try again!\n\n"
        f"Best,\nYour AI Travel Assistant"
    )

    # In production, use injected email client to dispatch the message
    # await ctx.deps.email_service.send(to=user_email, body=email_body)
    print(f"Outbound email sent to {recipient}:\n{email_body}")
    return "SUCCESS: Email sent. Stop processing immediately and return a BookingFailure state."

# Register a tool that the Agent can call when it's ready to execute
# The TripDetails parameter below is passed to the agent as a standard JSON schema.
@agent.tool
#def search_and_book(ctx: RunContext[AgentDependencies], trip: TripDetails) -> str: *** The TripDetails object seems to be confusing the agent
def search_and_book(ctx: RunContext[AgentDependencies], destination_city: str, meeting_date: str, arrival_date: str, departure_date: str) -> str:
    """Executes a live booking for a trip.

        ONLY call this tool if you have explicitly extracted the destination city and meeting date requirements.
        Do NOT call this tool multiple times for the same event.

        Args:
            destination_city: The name of the target destination city (e.g., 'Paris').
            meeting_date: The date of the meeting in ISO format (YYYY-MM-DD).
            arrival_date: The date of arrival in ISO format (YYYY-MM-DD).
            departure_date: The date of departure in ISO format (YYYY-MM-DD).
        """
    try:
        # Business logic validation before execution
        if not destination_city or not meeting_date:
            return "CRITICAL FAILURE: Missing required destination_city or meeting_date fields."

        # Execute booking components
        flights = ctx.deps.calendar_engine.search_and_book_flight(destination_city, meeting_date)
        hotel = ctx.deps.calendar_engine.search_and_book_hotel(destination_city, arrival_date, departure_date)
        taxi = ctx.deps.calendar_engine.search_and_book_taxi(destination_city, arrival_date)
              
        return f"{flights} | {hotel} | Taxi: {taxi}"
    
    except Exception as e:
        # Return the error text to Agent.
        # The error reason tells the model why it failed so it can use that info for the email.
        return f"CRITICAL FAILURE: Could not complete booking. Reason from system: {str(e)}"
    
    
    
calendar_agent = Agent(
    'ollama:gpt-oss:20b',
    output_type=CalendarChangeAnalysis,
    # system_prompt=(
    #     "You analyze calendar entries to assess whether the calendar entry is asking for a travel booking to be made."
    #     "A travel booking would usually include a return flight, a hotel and a taxi from the airport to the hotel."
    #     "It is NOT your job to make the booking, rather just assess if a booking is required."
    #     "Compare the title of the calendar event, as well as the text description to see if a meeting, flight or hotel is mentioned."
    #     "Not all calendar entries will relate to meetings, some calendar entries will be for reminders and will not require bookings."
    #     "CRITICAL: If the description contains text showing that flights/hotels are ALREADY booked "
    #     "or says '[AUTO-BOOKED]', you must set 'action_required' to 'ignore' to prevent loops."),
    retries=2
    )
               
