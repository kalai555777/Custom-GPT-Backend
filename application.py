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

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


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


def log_to_google_sheet(record: dict):
    """
    Append one row to Google Sheets.
    Columns (recommended):
    Timestamp | Name | Industry | Goals | Priority | Timeline | Budget Range | Main Contact
    """
    try:
        client = get_gsheet_client()
        if client is None:
            # No client (missing env var or error), skip logging
            return

        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)

        timestamp = datetime.datetime.utcnow().isoformat()

        name = record.get("name", "")
        industry = record.get("industry", "")
        goals = record.get("goals", "")
        priority = record.get("priority", "")
        timeline = record.get("timeline", "")
        budget_range = record.get("budget_range", "")
        main_contact = record.get("main_contact", "")

        # Each onboarding = one new row
        sheet.append_row([
            timestamp,
            name,
            industry,
            goals,
            priority,
            timeline,
            budget_range,
            main_contact
        ])
        print("Logged to Google Sheet:", name, industry, goals, priority, timeline, budget_range, main_contact)
    except Exception as e:
        # Do NOT crash the app, just log the error
        print("Error logging to Google Sheet:", e)


def build_summary(record: dict) -> str:
    """
    Build a project-manager-friendly onboarding summary
    with simple recommendation rules.
    """
    name = record.get("name", "Unknown Client")
    industry = record.get("industry", "Unknown Industry")
    goals = record.get("goals", "No goals provided")
    priority = record.get("priority")
    timeline = record.get("timeline")
    budget_range = record.get("budget_range")
    main_contact = record.get("main_contact")

    lines = []

    # Basic recap
    lines.append(f"Client Name: {name}")
    lines.append(f"Industry: {industry}")
    if main_contact:
        lines.append(f"Main Contact: {main_contact}")
    lines.append(f"Goals: {goals}")
    lines.append("")

    if priority:
        lines.append(f"Priority: {priority}")
    if timeline:
        lines.append(f"Timeline: {timeline}")
    if budget_range:
        lines.append(f"Budget Range: {budget_range}")
    lines.append("")

    lines.append("Recommended Next Steps:")
    lines.append("1. Schedule a kickoff meeting with the client.")
    lines.append("2. Clarify success metrics and key stakeholders.")
    lines.append("3. Finalize scope, timeline, and responsibilities.")
    lines.append("")

    # --- Simple rule-based recommendations ---

    # Priority-based
    if priority == "High":
        lines.append("Note: This is a HIGH-PRIORITY project; aim for kickoff within 1 week and weekly check-ins.")
    elif priority == "Medium":
        lines.append("Note: This is a MEDIUM-PRIORITY project; align milestones with the client’s existing roadmap.")
    elif priority == "Low":
        lines.append("Note: This is a LOW-PRIORITY project; consider bundling with other initiatives to save effort.")

    # Timeline-based
    if timeline == "1-3 months":
        lines.append("Timeline Suggestion: Short timeline — start with a focused MVP and clear 2–3 milestone phases.")
    elif timeline == "3-6 months":
        lines.append("Timeline Suggestion: Medium-term timeline — plan discovery, build, and rollout phases.")
    elif timeline == ">6 months":
        lines.append("Timeline Suggestion: Long-term timeline — consider phased delivery and periodic strategy reviews.")

    # Budget-based
    if budget_range == "<10k":
        lines.append("Budget Suggestion: Budget is limited — focus on low-cost, high-impact improvements and existing tools.")
    elif budget_range == "10k-50k":
        lines.append("Budget Suggestion: Mid-range budget — balance quick wins with 1–2 automation/tool investments.")
    elif budget_range == ">50k":
        lines.append("Budget Suggestion: Larger budget — consider a roadmap with discovery, pilot, and full rollout.")

    return "\n".join(lines)

def client_exists(name: str) -> bool:
    try:
        client = get_gsheet_client()
        if client is None:
            return False

        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        rows = sheet.get_all_records()

        # IMPORTANT: must match your header name exactly ("Name")
        for row in rows:
            if str(row.get("Name", "")).strip().lower() == name.strip().lower():
                return True

        return False
    except Exception as e:
        print("Error checking duplicates:", e)
        return False
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}

    record = {
        "name": data.get("name", "Unknown Client"),
        "industry": data.get("industry", "Unknown Industry"),
        "goals": data.get("goals", "No goals provided"),
        "priority": data.get("priority"),
        "timeline": data.get("timeline"),
        "budget_range": data.get("budget_range"),
        "main_contact": data.get("main_contact")
    }

    # ⭐ PREVENT DUPLICATES ⭐
    if client_exists(record["name"]):
        return jsonify({
            "response": f"A client named '{record['name']}' already exists in the system. No duplicate entry was created."
        })

    # Continue normally
    log_to_google_sheet(record)
    summary = build_summary(record)

    return jsonify({"response": summary})


@app.route("/find_client", methods=["POST"])
def find_client():
    """
    Search existing onboarding records in the Google Sheet by client name.
    Expects JSON: { "name": "some client" }
    """
    data = request.json or {}
    query = data.get("name", "").strip().lower()

    if not query:
        return jsonify({
            "status": "error",
            "message": "Please provide a 'name' field to search."
        }), 400

    client = get_gsheet_client()
    if client is None:
        return jsonify({
            "status": "error",
            "message": "Google Sheets client not available."
        }), 500

    try:
        sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
        rows = sheet.get_all_records()  # list of dicts, one per row

        # IMPORTANT: "Name" must match your header in row 1
        matches = [
            row for row in rows
            if query in str(row.get("Name", "")).strip().lower()
        ]

        return jsonify({
            "status": "success",
            "count": len(matches),
            "results": matches
        })
    except Exception as e:
        print("Error searching Google Sheet:", e)
        return jsonify({
            "status": "error",
            "message": "Error searching Google Sheet."
        }), 500

@app.route("/", methods=["GET"])
def home():
    return "Backend Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
