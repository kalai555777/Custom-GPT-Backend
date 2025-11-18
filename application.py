from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows OpenAI Custom GPT to call your backend

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    
    # Extract information sent by the user
    name = data.get("name", "Unknown Client")
    industry = data.get("industry", "Unknown Industry")
    goals = data.get("goals", "No goals provided")
    
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
