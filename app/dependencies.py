import os
from dataclasses import dataclass
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleCalendarEngine:
    def __init__(self, token_path: str = "token.json"):
        self.token_path = token_path
        self.scopes = ["https://www.googleapis.com/auth/calendar"]

    def get_authenticated_service(self):
        """Fetches a valid Google Calendar client, refreshing tokens dynamically."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Access Token expired. Refreshing tokens...")
                creds.refresh(Request())
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
            else:
                raise FileNotFoundError("Authentication missing. Please run generate_token.py.")

        return build("calendar", "v3", credentials=creds)
    
    
    def search_and_book_flight(self, destination_city, meeting_date):
        return ("flight_out_flightNo:XCVF456, flight_return_flightNo: FVCX567")
        
    
    def search_and_book_hotel(self, destination_city, arrival_date, departure_date):
        return "The Four Seasons, 5 stars"
        
    def search_and_book_taxi(self,destination_city, arrival_date):
        return "Big Yellow Cabs, ref: driver 'David' has been booked"

@dataclass
class AgentDependencies:
    calendar_engine: GoogleCalendarEngine
