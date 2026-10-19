from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional, Literal
from pydantic import BaseModel



class CalendarChangeAnalysis(BaseModel):
    action_required: Literal['book', 'cancel', 'ignore']
    extracted_city: Optional[str] = None
    extracted_date: Optional[str] = None
    change_summary: str

class BookingResult(BaseModel):
    destination_city: Optional[str] = None
    meeting_date: Optional[str] = None
    flight_booked: bool = False
    is_failed: bool = False
    fail_reason: Optional[str] = None
    
    
# #class TripDetails(BaseModel):
    
#     destination_city: str = Field(description="The city where the meeting/event takes place.")
#     meeting_date: date = Field(description="The date of the actual meeting.")
#     arrival_date: date = Field(description="The usually a day before the actual meeting.")
#     departure_date: date = Field(description="The usually a same day as the actual meeting.")
    
#     flight_out_date: date = Field(None, description="Flight departure date.")
#     flight_out_time: time = Field(description="The departure time .")
#     flight_out_airport: str = Field(description="The departure airport.")
#     flight_out_flightNo: str = Field(description="Either the departure flight booking ref, or the actual flight no if known")
    
#     flight_return_date: date = Field(None, description="Flight return date.")
#     flight_return_time: time = Field(description="The return time .")
#     flight_return_airport: str = Field(description="The return airport.")
#     flight_return_flightNo: str = Field(description="Either the return flight booking ref, or the actual flight no if known")
    
#     flight_booked: bool = False
#     hotel_booked: bool = False
#     taxi_booked: bool = False
    
#     # Failure fields if something goes wrong
#     is_failed: bool = Field(
#         default=False, 
#         description="Set to True ONLY if a tool failed or an email was sent."
#     )
#     error_message: Optional[str] = Field(
#         default=None, 
#         description="The reason why the booking failed, or details of the sent email."
#     )
    
#AgentOutputType = TripDetails
