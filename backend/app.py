import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
CORS(app)

# === Function to query OpenRouter ===
def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/mixtral-8x7b-instruct",  # 🔁 Change to other free models if needed
        "messages": [
            {"role": "system", "content": "You are an expert learning roadmap planner. Be concise, practical, and step-by-step."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        print("❌ OpenRouter Error:", response.status_code, response.text)
        return {"error": f"OpenRouter API error: {response.status_code}"}

    try:
        return response.json()
    except Exception as e:
        print("❌ JSON Parse Error:", str(e))
        return {"error": "Invalid JSON response from OpenRouter"}

# === API health check ===
@app.route("/")
def home():
    return jsonify({"message": "OpenRouter backend is running!"})

# === Main roadmap generator route ===
@app.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    data = request.get_json()
    goal = data.get("goal", "").strip()
    print("🎯 Goal:", goal)

    if not goal:
        return jsonify({"error": "Goal is required."}), 400

    prompt = f"""
    Create a personalized learning roadmap for someone who wants to: "{goal}".
    Keep it beginner-friendly, practical, and include real tools and skills to learn in order.
    Each step should be clear and achievable. Use bullet points or a numbered list.
    """

    try:
        response = query_openrouter(prompt)

        if "error" in response:
            return jsonify({"error": response["error"]}), 500

        roadmap = response["choices"][0]["message"]["content"]
        print("✅ Roadmap:", roadmap)
        return jsonify({"roadmap": roadmap})

    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

# === Run the app ===
if __name__ == "__main__":
    app.run(debug=True)
