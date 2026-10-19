# run_poller.py
import asyncio
import sys
from app.agents import calendar_agent, agent
from app.dependencies import AgentDependencies, GoogleCalendarEngine
import datetime
import logfire
import traceback
import json
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart



# 1. Configure logfire to ONLY output to the terminal console
logfire.configure(send_to_logfire='never')

# 2. Instrument Pydantic AI
logfire.instrument_pydantic_ai()


# 1. Initialize long-lived dependencies
calendar_engine = GoogleCalendarEngine()
live_deps = AgentDependencies(calendar_engine=calendar_engine)


async def check_and_process_calendar(token_file: str):
    '''
        The events are being polled from a google calendar - the first agent asseses whether a travel booking is required, 
        and if so passes the calendar details to a second agent for the booking to be made.
    '''

    try:
        
        # Instantiate the calendar engine specifically for this account file
        calendar_engine = GoogleCalendarEngine(token_file)
        live_deps = AgentDependencies(calendar_engine=calendar_engine)
        
        service = calendar_engine.get_authenticated_service()
    except Exception as auth_err:
        print(f"Auth Error: {auth_err}")
        sys.exit(1)
        
        
    # ADD DIAGNOSTIC LINES HERE:
    current_calendar_meta = service.calendars().get(calendarId='primary').execute()
    print(f"IDENTITY CHECK: This script is currently reading the calendar for: {current_calendar_meta.get('id')}")
    
    # Fetch the most recently updated event from Google Calendar
    # Only pull items modified in the last 24 hours to focus purely on active events     
    # Focus only on events that take place from right now into the future
    current_time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    print("Querying upcoming scheduled calendar events...")
    events_result = service.events().list(
        calendarId='primary', 
        maxResults=20,                 # Scan the next 20 upcoming events
        singleEvents=True,             # Expand recurring series into distinct items
        timeMin=current_time_iso,      # Look from this exact minute
        orderBy='startTime'            # Sort by meeting time (ascending)
    ).execute()
    
    # this call returns an array of calendar events
    events = events_result.get('items', [])
    print(f"Google API response: Found {len(events)} event instances in the last 24 hours.")
    
    if not events:
        return
        
    # create a unique set of event ids if we hae a problem with reoccuring meetings.
    processed_texts = set()
        
        
    for event in reversed(events):
        owner_email = event.get('organizer', {}).get('email', event.get('creator', {}).get('email'))
        if not owner_email:
            owner_email = "default_admin@bigcompany.com" # Fallback if fields are missing
        
        title = event.get('summary', '').lower()
        #raw_text = event.get('description', '').strip()
        
        # Safely pull nested date fields
        start_time = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'No Start Time'))
        end_time = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'No End Time'))
        description = event.get('description', 'No description text provided.')

        print("\n--- LIVE TRACKED EVENT ---")
        print(f"Title:       {title}")
        print(f"Start:       {start_time}")
        print(f"End:         {end_time}")
        print(f"Description: {description.strip()}")
        print("-----------------------------\n")        
        
        # 1. HARD FILTER: Automatically skip anything created by the Duolingo app
        if "duolingo" in title or "duolingo" in description.lower():
            print ("Duolingo found, skipping...")
            continue
            
        # 2. DUPLICATION: Skip if we already saw this exact text on this pass
        if description in processed_texts:
            print("This one looks to be a duplicate, skipping...")
            continue
        if description:
            processed_texts.add(description)
        
        # 3. Skip booking if empty or already processed by our agents previously
        if not description or "[AUTO-BOOKED]" in description:
            print("Previously booked, skipping")
            continue
            
        print(f"\nFound unique, valid description text: \"{description}\", this will be passed to analysis agent.")
        
        # Run Agent 1: The Analyzer
        analysis_result = await calendar_agent.run(f"Analyze: Event title: {title}, Event descriptions:{description}")
        analysis = analysis_result.output
        print(f"Analysis: Action={analysis.action_required}. Summary: {analysis.change_summary}")
        
        # Run Agent 2: The Booker
        if analysis.action_required == 'book':
                    
            print(f"Triggering Booking Agent for {analysis.extracted_city}...\n")
            
            dt_object = datetime.datetime.fromisoformat(start_time)
            datestr = dt_object.strftime("%B %d, %Y at %H:%M")
            bookingstr = f"Please Book flight to {analysis.extracted_city} for a meeting that starts on {datestr}. A hotel in the area of the meeting and taxi to the hotel from the airport will also need to be booked. Do not book a taxi back to the airport for after the meeting."
            
            print(f"This is the user prompt:{bookingstr}\n") 
            
            sys_prompt=(f"You are a travel booking assistant. Your job is to book travel for a given meeting date.\n\n"
                    "CRITICAL RULES:\n"
                    "1. The company office is based in London and you must choose the airport to use, for example: choose London Heathrow Airport for a long haul flight, "
                    "choose London City Airport for short flights, or choose London Gatwick Airport for all other options.\n"
                    "2. The date of the meeting should be the same as the departure date for the flight. If the meeting is in the morning, then the departure date for the return flight will be the same day as the meeting. If the meeting is in the afternoon, then the return flight will be the morning after the meeting.\n"
                    "3. If you encounter any critical failures while executing 'search_and_book', you must immediately "
                    f"call 'send_clarification_email' to notify {owner_email}.\n"
                    "4. Once 'send_clarification_email' has been executed, you must IMMEDIATELY stop calling tools and "
                    "BookingResult object by setting 'is_failed' to True and giving a reason for the failure by updating the 'fail_reason' object value. Do not attempt to book anything else."
                )
            
                    
            print(f"This is the system prompt:{sys_prompt}\n")
                            
            #  DON'T CALL AGENT UNTIL DEBUGGING IS THROUGH           
            booking_result = await agent.run( 
                instructions = sys_prompt,
                user_prompt=bookingstr,
                deps=live_deps
            )
            
            booking = booking_result.output
            
            if booking.is_failed:
                print (f"There was a booking problem {booking.fail_reason}")
            else:
                confirmation_text = (
                    f"{description}\n\n"
                    f"[AUTO-BOOKED]\n"
                    f"Destination: {booking.destination_city} | Status: Confirmed"
                )
                
                event['description'] = confirmation_text
                service.events().update(calendarId='primary', eventId=event.get('id'), body=event).execute()
                print("Google Calendar entry updated successfully!")
                
                
                
                
            print("\n================= AGENT EXECUTION HISTORY =================")
            
            for index, message in enumerate(booking_result.all_messages(), 1):
                print(f"\n[Step {index}] ", end="")
                
                # 1. Handle incoming requests/instructions from the user or framework
                if isinstance(message, ModelRequest):
                    print("FRAMEWORK / USER REQUEST:")
                    for part in message.parts:
                        if isinstance(part, UserPromptPart):  # If it's a standard string prompt
                            print(f"  Prompt: \"{part.content}\"")
                        elif isinstance(part, ToolReturnPart): # If it's data coming back from a tool
                            print(f"Tool '{part.tool_name}' returned: {part.content}")

                # 2. Handle actions the LLM decided to take
                elif isinstance(message, ModelResponse):
                    print("MODEL RESPONSE:")
                    print(booking.model_dump_json(indent=2))
                    
                    for part in message.parts:
                        if isinstance(part, TextPart) and part.content.strip():
                            pass
                                    
                        elif isinstance(part, ToolCallPart): # If the model calls a tool
                            print(f"Called Tool: '{part.tool_name}' with args: {part.args}")

            print("\n===========================================================")
            
            break




# 2. Update the main() loop at the bottom to look exactly like this:
async def main():
    
    print("Travel Agent Poller Started.")
    print("Checking live Google Calendars every 30 seconds. Press CTRL+C to stop.\n")
    
    while True:    
        try:
            
            # Define the list of active account passports you want to manage
            accounts_to_monitor = ["token_primary.json", "token_test.json"]
        
            print("Multi-User Auto-Booking Travel Agent Poller Started.")
            print(f"Monitoring accounts: {accounts_to_monitor} sequentially.\n")
            
            # Run the processing logic
            for token_file in accounts_to_monitor:
                await check_and_process_calendar(token_file)
            
            await asyncio.sleep(30)
                
        except Exception as e:
            print("CRITICAL LOOP ERROR DETECTED! Printing full traceback:")
            # This forces Python to print the exact file line that failed
            traceback.print_exc() 
            print("----------------------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(main())
