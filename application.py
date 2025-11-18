from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import datetime

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
CORS(app)

# --- Google Sheets setup ---

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gsheet_client():
    # Load service account JSON from environment variable
    service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

# Change this to your actual spreadsheet name and sheet name
SPREADSHEET_NAME = "Client Onboarding"  # <- Google Sheet name
WORKSHEET_NAME = "Sheet1"               # <- Tab name at the bottom

def log_to_google_sheet(name, industry, goals):
    try:
        client = get_gsheet_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

        timestamp = datetime.datetime.utcnow().isoformat()

        # Each onboarding = one new row
        sheet.append_row([timestamp, name, industry, goals])
    except Exception as e:
        # Just print error so your API still works even if Sheets fails
        print("Error logging to Google Sheet:", e)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    
    # Extract information sent by the GPT / user
    name = data.get("name", "Unknown Client")
    industry = data.get("industry", "Unknown Industry")
    goals = data.get("goals", "No goals provided")

    # 🔹 Save to Google Sheet
    log_to_google_sheet(name, industry, goals)
    
    # 🔹 Build onboarding summary (same as before)
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
