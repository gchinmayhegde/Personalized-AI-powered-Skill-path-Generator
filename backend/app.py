import os
import json
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import time

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

# ✅ Improved YouTube video fetching with better filtering
def fetch_youtube_videos(query, max_results=3):
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        
        # Enhanced query for better filtering
        enhanced_query = f"{query} tutorial learning course -shorts -short"
        
        params = {
            "part": "snippet",
            "q": enhanced_query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results * 2,  # Get more to filter out shorts
            "type": "video",
            "videoDuration": "medium",  # Filter out very short videos
            "order": "relevance",
            "safeSearch": "strict"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            videos = []
            for item in response.json().get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                description = item["snippet"]["description"]
                
                # Filter out shorts and irrelevant content
                if (not any(keyword in title.lower() for keyword in ["#shorts", "short", "tiktok", "reel"]) and
                    len(description) > 50 and  # Ensure decent description length
                    any(keyword in title.lower() for keyword in ["tutorial", "learn", "course", "guide", "how to", "explained"])):
                    
                    link = f"https://www.youtube.com/watch?v={video_id}"
                    videos.append({"title": title, "link": link})
                    
                    if len(videos) >= max_results:
                        break
            
            return videos[:max_results]
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
            "q": f"site:medium.com {query} tutorial guide",
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

# ✅ New function to fetch Coursera courses
def fetch_coursera_courses(query, max_results=2):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": f"site:coursera.org {query} course specialization",
            "num": max_results
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get("organic", [])[:max_results]:
                if "coursera.org" in item.get("link", ""):
                    courses.append(item.get("link"))
            return courses
        else:
            print("❌ Coursera Fetch Error:", response.text)
            return []
    except Exception as e:
        print("❌ Coursera Fetch Exception:", e)
        return []

# ✅ New function to fetch Udemy courses
def fetch_udemy_courses(query, max_results=2):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": f"site:udemy.com {query} course",
            "num": max_results
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get("organic", [])[:max_results]:
                if "udemy.com" in item.get("link", ""):
                    courses.append(item.get("link"))
            return courses
        else:
            print("❌ Udemy Fetch Error:", response.text)
            return []
    except Exception as e:
        print("❌ Udemy Fetch Exception:", e)
        return []

@app.route("/")
def home():
    return jsonify({"message": "Backend running with streaming support!"})

@app.route("/generate-roadmap", methods=["POST", "GET"])
def generate_roadmap():
    try:
        # Handle both POST and GET requests for streaming
        if request.method == "GET":
            goal = request.args.get("goal", "").strip()
        else:
            data = request.json
            goal = data.get("goal", "").strip()
            
        if not goal:
            return jsonify({"error": "Goal is required"}), 400

        print(f"🎯 Goal: {goal}")

        def generate_streaming_response():
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating roadmap...'})}\n\n"
            
            # ✅ Generate roadmap using OpenRouter
            prompt = f"Create a concise step-by-step learning roadmap for: {goal}. Use 5-7 steps. Format each step as a clear, actionable title without numbering."
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            try:
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
                    yield f"data: {json.dumps({'type': 'error', 'message': f'OpenRouter API failed: {response.text}'})}\n\n"
                    return

                roadmap_text = response.json()["choices"][0]["message"]["content"]
                print(f"📝 Generated roadmap text: {roadmap_text}")
                
                # Clean and parse steps
                steps = [step.strip() for step in roadmap_text.split("\n") if step.strip()]
                print(f"📋 Parsed steps: {steps}")

                # Send roadmap structure
                yield f"data: {json.dumps({'type': 'roadmap_generated', 'steps': steps})}\n\n"

                # Process each step and stream resources as they're found
                for i, step in enumerate(steps):
                    if step:
                        step_data = {
                            "step": step,
                            "resources": {"youtube": [], "blogs": [], "courses": []}
                        }
                        
                        print(f"🔍 Processing step {i+1}: {step}")
                        
                        # Send step start
                        yield f"data: {json.dumps({'type': 'step_start', 'index': i, 'step': step})}\n\n"

                        # Fetch YouTube videos
                        try:
                            youtube_links = fetch_youtube_videos(step)
                            step_data["resources"]["youtube"] = [video["link"] for video in youtube_links]
                            print(f"📺 Found {len(youtube_links)} YouTube videos")
                            
                            # Stream YouTube results immediately
                            yield f"data: {json.dumps({'type': 'resources_update', 'index': i, 'resource_type': 'youtube', 'data': step_data['resources']['youtube']})}\n\n"
                        except Exception as e:
                            print(f"❌ YouTube error for step {i+1}: {e}")

                        # Fetch Medium blogs
                        try:
                            medium_links = fetch_medium_articles(step)
                            step_data["resources"]["blogs"] = [article["link"] for article in medium_links]
                            print(f"📖 Found {len(medium_links)} Medium articles")
                            
                            # Stream blog results immediately
                            yield f"data: {json.dumps({'type': 'resources_update', 'index': i, 'resource_type': 'blogs', 'data': step_data['resources']['blogs']})}\n\n"
                        except Exception as e:
                            print(f"❌ Medium error for step {i+1}: {e}")

                        # Fetch real-time courses (Coursera + Udemy + static)
                        try:
                            # Get Coursera courses
                            coursera_courses = fetch_coursera_courses(step, 1)
                            
                            # Get Udemy courses
                            udemy_courses = fetch_udemy_courses(step, 1)
                            
                            # Get static courses via similarity
                            query_embedding = model.encode(step, convert_to_tensor=True)
                            similarities = util.pytorch_cos_sim(query_embedding, resource_embeddings)[0]
                            top_indices = similarities.argsort(descending=True)[:1]
                            static_courses = []
                            for idx in top_indices:
                                matched = resources[int(idx)]
                                static_courses.extend(matched["courses"])
                            
                            # Combine all courses
                            all_courses = coursera_courses + udemy_courses + static_courses[:1]
                            step_data["resources"]["courses"] = all_courses[:2]  # Limit to 2 courses
                            
                            print(f"📘 Found {len(all_courses)} courses")
                            
                            # Stream course results immediately
                            yield f"data: {json.dumps({'type': 'resources_update', 'index': i, 'resource_type': 'courses', 'data': step_data['resources']['courses']})}\n\n"
                        except Exception as e:
                            print(f"❌ Courses error for step {i+1}: {e}")

                        # Send step completion
                        yield f"data: {json.dumps({'type': 'step_complete', 'index': i})}\n\n"

                # Send completion message
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"

            except Exception as e:
                print(f"❌ Exception in roadmap generation: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return Response(
            generate_streaming_response(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )

    except Exception as e:
        print(f"❌ Exception in generate_roadmap: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)