from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/process-onboarding", methods=["POST"])
def process_onboarding():
    data = request.json

    name = data.get("name")
    goals = data.get("goals")
    industry = data.get("industry")

    summary = f"""
Client Name: {name}
Industry: {industry}
Goals: {goals}

Recommended Next Steps:
1. Kickoff meeting
2. Requirement gathering
3. Model selection and scoping
"""

    return jsonify({"summary": summary})

@app.route("/", methods=["GET"])
def home():
    return "Backend Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)