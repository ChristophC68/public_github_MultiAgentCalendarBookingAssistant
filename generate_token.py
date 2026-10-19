import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

# Access them securely
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

# Request full read/write access to the calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def generate_named_token(account_label: str):
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=8500, prompt="consent", access_type="offline")
    #creds = flow.run_local_server(port=0, prompt="consent", access_type="offline") # don't specify a port, let the operating system find an empty port because on the first call, that port gets locked for 60 seconds. 
    
    filename = f"token_{account_label}.json"
    with open(filename, "w") as token_file:
        token_file.write(creds.to_json())
    print(f"Success! Generated passport file: {filename}")

# def run_authentication():
#     if not os.path.exists("credentials.json"):
#         raise FileNotFoundError("Missing credentials.json in root folder!")
        
#     print("Initializing Google Authentication Flow...")
#     flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    
#     # Run a local temporary server to catch Google's secure login redirect signal
#     # We use port 8500 to match the Authorized Redirect URI you registered!
#     creds = flow.run_local_server(port=8500, prompt="consent", access_type="offline")
    
#     # Save the credentials token file
#     with open("token.json", "w") as token_file:
#         token_file.write(creds.to_json())
        
#     print("\nSUCCESS! token.json has been generated in your root directory.")
#     print("Your app now has persistent, automated access to your test calendar.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a label. Example: python generate_token.py primary")
        sys.exit(1)
    generate_named_token(sys.argv[1])

# if __name__ == "__main__":
#     run_authentication()
