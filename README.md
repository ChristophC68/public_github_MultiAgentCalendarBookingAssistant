This project works from Google Platform using OAuth to connect to different users' Calendars. The details for setting up OAuth, and obtaining the secrets key are not included here. However, once those tasks have been completed, the generate_token.py will be useful. Please also look at the .env.example file to use as the basis for your own .env file where you can add you specific settings. 

The main python script (run_poller.py) does not use a UI, at the moment it sends lots of output info to the terminal. The script polls the calendars looking for meetings that need flights to be booked for the meeting. It assumes that the origin office is in London, and then proceeds to book a return flight, one-way taxi and a hotel. 

Of course the actual bookings are hard coded .... no need to input credit card details :-)

There are two agents, one to analyse the calendar meeting, and if it is suitable to need a booking (not all calendar entries are for meetings abroad), it passes the meeting details to another agent for the booking. 
At the end of the booking the Calendar entry is updated so that no further bookings for this meeting take place. This all works smoothly for the two test accounts that I have been using. 

Thanks for looking.

