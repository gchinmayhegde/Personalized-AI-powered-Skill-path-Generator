import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# ✅ Initialize Flask
app = Flask(__name__)
CORS(app)

# ✅ Load Hugging Face model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# ✅ Load static resource dataset for courses only
RESOURCE_FILE = "resources.json"
with open(RESOURCE_FILE, "r", encoding="utf-8") as f:
    resources = json.load(f)["resources"]

# ✅ Precompute resource embeddings
resource_texts = [res["topic"] for res in resources]
resource_embeddings = model.encode(resource_texts, convert_to_tensor=True)

# ✅ Fetch YouTube videos
def fetch_youtube_videos(query, max_results=2):
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results,
            "type": "video"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            videos = []
            for item in response.json().get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                link = f"https://www.youtube.com/watch?v={video_id}"
                videos.append({"title": title, "link": link})
            return videos
        else:
            print("❌ YouTube API Error:", response.text)
            return []
    except Exception as e:
        print("❌ YouTube Exception:", e)
        return []

# ✅ Fetch Medium blogs using Serper API
def fetch_medium_articles(query, max_results=2):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": f"site:medium.com {query}",
            "num": max_results
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for item in data.get("organic", [])[:max_results]:
                articles.append({"title": item.get("title"), "link": item.get("link")})
            return articles
        else:
            print("❌ Serper API Error:", response.text)
            return []
    except Exception as e:
        print("❌ Medium Fetch Exception:", e)
        return []

@app.route("/")
def home():
    return jsonify({"message": "Backend running with YouTube + Medium + Hugging Face!"})

@app.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    try:
        data = request.json
        goal = data.get("goal", "").strip()
        if not goal:
            return jsonify({"error": "Goal is required"}), 400

        print(f"🎯 Goal: {goal}")

        # ✅ Generate roadmap using OpenRouter
        prompt = f"Create a concise step-by-step learning roadmap for: {goal}. Use 5-7 steps. Format each step as a clear, actionable title without numbering."
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            }
        )

        if response.status_code != 200:
            print(f"❌ OpenRouter API Error: {response.text}")
            return jsonify({"error": f"OpenRouter API failed: {response.text}"}), 500

        roadmap_text = response.json()["choices"][0]["message"]["content"]
        print(f"📝 Generated roadmap text: {roadmap_text}")
        
        # Clean and parse steps
        steps = [step.strip() for step in roadmap_text.split("\n") if step.strip()]
        print(f"📋 Parsed steps: {steps}")

        roadmap = []
        for step in steps:
            if step:
                # FIXED: Use 'step' instead of 'title' to match frontend expectations
                roadmap.append({"step": step, "resources": {"youtube": [], "blogs": [], "courses": []}})

        # ✅ Add YouTube, Medium, and courses for each step
        for i, item in enumerate(roadmap):
            query = item["step"]
            print(f"🔍 Processing step {i+1}: {query}")

            # YouTube videos
            try:
                youtube_links = fetch_youtube_videos(query)
                item["resources"]["youtube"] = [video["link"] for video in youtube_links]
                print(f"📺 Found {len(youtube_links)} YouTube videos")
            except Exception as e:
                print(f"❌ YouTube error for step {i+1}: {e}")
                item["resources"]["youtube"] = []

            # Medium blogs
            try:
                medium_links = fetch_medium_articles(query)
                item["resources"]["blogs"] = [article["link"] for article in medium_links]
                print(f"📖 Found {len(medium_links)} Medium articles")
            except Exception as e:
                print(f"❌ Medium error for step {i+1}: {e}")
                item["resources"]["blogs"] = []

            # Courses via Hugging Face similarity
            try:
                query_embedding = model.encode(query, convert_to_tensor=True)
                similarities = util.pytorch_cos_sim(query_embedding, resource_embeddings)[0]
                top_indices = similarities.argsort(descending=True)[:2]
                courses = []
                for idx in top_indices:
                    matched = resources[int(idx)]
                    courses.extend(matched["courses"])
                item["resources"]["courses"] = courses[:2]  # Limit to 2 courses
                print(f"📘 Found {len(courses)} courses")
            except Exception as e:
                print(f"❌ Courses error for step {i+1}: {e}")
                item["resources"]["courses"] = []

        print(f"✅ Final roadmap: {roadmap}")
        return jsonify({"roadmap": roadmap})

    except Exception as e:
        print(f"❌ Exception in generate_roadmap: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)