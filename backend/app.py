import os
import json
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
import time
import re

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

# ✅ Enhanced skill categorization for better resource matching
PHYSICAL_SKILLS = [
    "pilot", "flying", "aviation", "aircraft", "cockpit", "flight training",
    "driving", "cooking", "chef", "culinary", "sports", "fitness", "gym",
    "dance", "music instrument", "guitar", "piano", "violin", "drums",
    "surgery", "medical procedure", "laboratory", "welding", "carpentry",
    "plumbing", "electrical work", "massage", "yoga instructor"
]

CREATIVE_SKILLS = [
    "design", "ui/ux", "graphic design", "art", "drawing", "painting",
    "photography", "video editing", "animation", "3d modeling",
    "writing", "copywriting", "content creation", "blogging"
]

TECH_SKILLS = [
    "programming", "coding", "web development", "app development",
    "data science", "machine learning", "ai", "cybersecurity",
    "blockchain", "cloud computing", "devops", "database", "sql"
]

def categorize_skill(goal):
    """Categorize the skill to provide better resource recommendations"""
    goal_lower = goal.lower()
    
    if any(skill in goal_lower for skill in PHYSICAL_SKILLS):
        return "physical"
    elif any(skill in goal_lower for skill in CREATIVE_SKILLS):
        return "creative"
    elif any(skill in goal_lower for skill in TECH_SKILLS):
        return "technical"
    else:
        return "general"

def get_contextual_message(skill_category, step):
    """Provide contextual messages for different skill categories"""
    step_lower = step.lower()
    
    if skill_category == "physical":
        if any(word in step_lower for word in ["training", "practice", "hands-on", "flight", "practical"]):
            return {
                "message": "🎯 This step requires hands-on practice and may need in-person training or certification.",
                "suggestion": "Look for local training centers, certified instructors, or official institutions in your area."
            }
    
    return None

# ✅ Enhanced YouTube video fetching with playlist detection and better filtering
def fetch_youtube_videos(query, max_results=3, skill_category="general"):
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        
        # Enhanced query based on skill category
        if skill_category == "creative" and "figma" in query.lower():
            enhanced_query = f"{query} complete course tutorial playlist -shorts"
        elif skill_category == "technical":
            enhanced_query = f"{query} full course tutorial playlist -shorts -short"
        elif skill_category == "physical":
            enhanced_query = f"{query} training guide tutorial -shorts -vlog"
        else:
            enhanced_query = f"{query} tutorial learning course playlist -shorts -short"
        
        params = {
            "part": "snippet",
            "q": enhanced_query,
            "key": YOUTUBE_API_KEY,
            "maxResults": max_results * 3,  # Get more to filter better
            "type": "video",
            "videoDuration": "medium",
            "order": "relevance",
            "safeSearch": "strict"
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            videos = []
            items = response.json().get("items", [])
            
            # Prioritize playlists and longer videos
            playlist_videos = []
            course_videos = []
            regular_videos = []
            
            for item in items:
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                description = item["snippet"]["description"]
                channel_title = item["snippet"]["channelTitle"]
                
                # Filter out unwanted content
                if any(keyword in title.lower() for keyword in 
                       ["#shorts", "short", "tiktok", "reel", "meme", "reaction"]):
                    continue
                
                # Check if it's part of a playlist or course
                if any(keyword in title.lower() for keyword in 
                       ["playlist", "complete course", "full course", "masterclass", "bootcamp"]):
                    playlist_videos.append({
                        "title": title,
                        "link": f"https://www.youtube.com/watch?v={video_id}",
                        "channel": channel_title,
                        "type": "course"
                    })
                elif any(keyword in title.lower() for keyword in 
                         ["tutorial", "learn", "guide", "explained", "crash course"]):
                    course_videos.append({
                        "title": title,
                        "link": f"https://www.youtube.com/watch?v={video_id}",
                        "channel": channel_title,
                        "type": "tutorial"
                    })
                else:
                    regular_videos.append({
                        "title": title,
                        "link": f"https://www.youtube.com/watch?v={video_id}",
                        "channel": channel_title,
                        "type": "video"
                    })
            
            # Prioritize playlist/course videos, then tutorials, then regular videos
            all_videos = playlist_videos + course_videos + regular_videos
            return all_videos[:max_results]
        
        else:
            print("❌ YouTube API Error:", response.text)
            return []
    except Exception as e:
        print("❌ YouTube Exception:", e)
        return []

# ✅ Enhanced Medium blog fetching with better filtering
def fetch_medium_articles(query, max_results=2, skill_category="general"):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Enhanced search query based on skill category
        if skill_category == "physical":
            search_query = f"site:medium.com {query} guide training tips"
        else:
            search_query = f"site:medium.com {query} tutorial guide complete"
        
        payload = {
            "q": search_query,
            "num": max_results * 2
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for item in data.get("organic", [])[:max_results]:
                # Filter out low-quality articles
                title = item.get("title", "").lower()
                if not any(unwanted in title for unwanted in ["newsletter", "subscription", "follow me"]):
                    articles.append({
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet", "")
                    })
            return articles
        else:
            print("❌ Serper API Error:", response.text)
            return []
    except Exception as e:
        print("❌ Medium Fetch Exception:", e)
        return []

# ✅ Enhanced Coursera course fetching with direct course links
def fetch_coursera_courses(query, max_results=2, skill_category="general"):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        # More specific search for actual course pages
        search_query = f"site:coursera.org/learn {query} OR site:coursera.org/specializations {query}"
        
        payload = {
            "q": search_query,
            "num": max_results * 2
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get("organic", [])[:max_results]:
                link = item.get("link", "")
                # Only include direct course or specialization links
                if ("/learn/" in link or "/specializations/" in link) and "coursera.org" in link:
                    courses.append({
                        "title": item.get("title", ""),
                        "link": link,
                        "snippet": item.get("snippet", "")
                    })
            return [course["link"] for course in courses]
        else:
            print("❌ Coursera Fetch Error:", response.text)
            return []
    except Exception as e:
        print("❌ Coursera Fetch Exception:", e)
        return []

# ✅ Enhanced Udemy course fetching with direct course links
def fetch_udemy_courses(query, max_results=2, skill_category="general"):
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        # More specific search for actual course pages
        search_query = f"site:udemy.com/course {query} complete"
        
        payload = {
            "q": search_query,
            "num": max_results * 2
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            courses = []
            for item in data.get("organic", [])[:max_results]:
                link = item.get("link", "")
                # Only include direct course links, not category or search pages
                if "/course/" in link and "udemy.com" in link and not any(x in link for x in ["/search/", "/courses/"]):
                    courses.append({
                        "title": item.get("title", ""),
                        "link": link,
                        "snippet": item.get("snippet", "")
                    })
            return [course["link"] for course in courses]
        else:
            print("❌ Udemy Fetch Error:", response.text)
            return []
    except Exception as e:
        print("❌ Udemy Fetch Exception:", e)
        return []

@app.route("/")
def home():
    return jsonify({"message": "Enhanced Backend with better resource matching!"})

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
        
        # Categorize the skill
        skill_category = categorize_skill(goal)
        print(f"📂 Skill Category: {skill_category}")

        def generate_streaming_response():
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing your goal and generating roadmap...'})}\n\n"
            
            # ✅ Generate roadmap using OpenRouter
            prompt = f"Create a concise step-by-step learning roadmap for: {goal}. Use 5-7 steps. Format each step as a clear, actionable title without numbering. Focus on practical learning progression."
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
                            {"role": "system", "content": "You are a helpful AI assistant that creates practical learning roadmaps."},
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
                            "resources": {"youtube": [], "blogs": [], "courses": []},
                            "contextual_info": None
                        }
                        
                        print(f"🔍 Processing step {i+1}: {step}")
                        
                        # Send step start
                        yield f"data: {json.dumps({'type': 'step_start', 'index': i, 'step': step})}\n\n"

                        # Check for contextual messages
                        contextual_info = get_contextual_message(skill_category, step)
                        if contextual_info:
                            yield f"data: {json.dumps({'type': 'contextual_info', 'index': i, 'info': contextual_info})}\n\n"

                        # Fetch YouTube videos with enhanced filtering
                        try:
                            youtube_videos = fetch_youtube_videos(step, skill_category=skill_category)
                            step_data["resources"]["youtube"] = [video["link"] for video in youtube_videos]
                            print(f"📺 Found {len(youtube_videos)} YouTube videos")
                            
                            # Stream YouTube results immediately with metadata
                            yield f"data: {json.dumps({'type': 'resources_update', 'index': i, 'resource_type': 'youtube', 'data': step_data['resources']['youtube'], 'metadata': youtube_videos})}\n\n"
                        except Exception as e:
                            print(f"❌ YouTube error for step {i+1}: {e}")

                        # Fetch Medium blogs with better filtering
                        try:
                            medium_articles = fetch_medium_articles(step, skill_category=skill_category)
                            step_data["resources"]["blogs"] = [article["link"] for article in medium_articles]
                            print(f"📖 Found {len(medium_articles)} Medium articles")
                            
                            # Stream blog results immediately with metadata
                            yield f"data: {json.dumps({'type': 'resources_update', 'index': i, 'resource_type': 'blogs', 'data': step_data['resources']['blogs'], 'metadata': medium_articles})}\n\n"
                        except Exception as e:
                            print(f"❌ Medium error for step {i+1}: {e}")

                        # Fetch enhanced courses
                        try:
                            # Get Coursera courses
                            coursera_courses = fetch_coursera_courses(step, skill_category=skill_category)
                            
                            # Get Udemy courses
                            udemy_courses = fetch_udemy_courses(step, skill_category=skill_category)
                            
                            # Get static courses via similarity (as fallback)
                            query_embedding = model.encode(step, convert_to_tensor=True)
                            similarities = util.pytorch_cos_sim(query_embedding, resource_embeddings)[0]
                            top_indices = similarities.argsort(descending=True)[:1]
                            static_courses = []
                            for idx in top_indices:
                                matched = resources[int(idx)]
                                static_courses.extend(matched.get("courses", []))
                            
                            # Prioritize direct course links over static ones
                            all_courses = coursera_courses + udemy_courses
                            if not all_courses:  # Only use static if no direct courses found
                                all_courses = static_courses[:1]
                            
                            step_data["resources"]["courses"] = all_courses[:2]  # Limit to 2 courses
                            
                            print(f"📘 Found {len(all_courses)} courses")
                            
                            # Add contextual message if no online courses available for physical skills
                            if skill_category == "physical" and not all_courses:
                                contextual_message = "💡 This skill requires hands-on practice. Consider finding local training centers or certified instructors."
                                yield f"data: {json.dumps({'type': 'no_online_courses', 'index': i, 'message': contextual_message})}\n\n"
                            
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