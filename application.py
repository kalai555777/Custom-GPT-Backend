from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows OpenAI Custom GPT to call your backend

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    
    # You can still include your onboarding logic or mock GPT response
    response = f"Mock GPT response to: {user_message}"

    return jsonify({"response": response})

@app.route("/", methods=["GET"])
def home():
    return "Backend Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
