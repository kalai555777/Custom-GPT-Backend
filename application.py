
from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import datetime
app = Flask(__name__)
CORS(app)  # allows OpenAI Custom GPT to call your backend
# --- Google Sheets setup (safe) ---

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_client():
    """
    Safely get a Google Sheets client.
    If GOOGLE_SERVICE_ACCOUNT_JSON is missing or invalid,
    this will return None and not crash the app.
    """
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("GOOGLE_SERVICE_ACCOUNT_JSON is not set. Skipping Google Sheets logging.")
        return None

    try:
        service_account_info = json.loads(service_account_json)
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print("Error creating Google Sheets client:", e)
        return None

# Change this to your actual spreadsheet name and sheet name
SPREADSHEET_NAME = "Client Onboarding"  # Google Sheet title (top)
WORKSHEET_NAME = "Sheet1"               # Tab name at the bottom

def log_to_google_sheet(name, industry, goals):
    """
    Try to append one row to Google Sheets.
    If anything goes wrong, just print an error and continue.
    """
    try:
        client = get_gsheet_client()
        if client is None:
            # No client (missing env var or error), skip logging
            return

        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

        timestamp = datetime.datetime.utcnow().isoformat()

        # Each onboarding = one new row
        sheet.append_row([timestamp, name, industry, goals])
        print("Logged to Google Sheet:", name, industry, goals)
    except Exception as e:
        # Do NOT crash the app, just log the error
        print("Error logging to Google Sheet:", e)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    
    # Extract information sent by the user
    name = data.get("name", "Unknown Client")
    industry = data.get("industry", "Unknown Industry")
    goals = data.get("goals", "No goals provided")
    
    # NEW: log to Google Sheet (safely)
    log_to_google_sheet(name, industry, goals)
    # Build onboarding summary
    summary = f"""
Client Name: {name}
Industry: {industry}
Goals: {goals}

Recommended Next Steps:
1. Kickoff meeting
2. Requirement gathering
3. Model selection and scoping
"""
    
    return jsonify({"response": summary.strip()})

@app.route("/", methods=["GET"])
def home():
    return "Backend Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
