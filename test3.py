import requests
from flask import Flask, render_template, request

app = Flask(__name__)
YOUTUBE_API_KEY = "AIzaSyCeGO0u9fwuCyIysgYfNHuGsxCOgpdj6t0"  # Replace with your actual API key
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def get_plant_videos(plant_name):
    params = {
        "part": "snippet",
        "q": f"how to grow {plant_name}",
        "key": YOUTUBE_API_KEY,
        "maxResults": 3,
        "type": "video"
    }
    
    response = requests.get(YOUTUBE_SEARCH_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        videos = data.get("items", [])
        return [{"title": v["snippet"]["title"], "videoId": v["id"]["videoId"]} for v in videos]
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    videos = []
    if request.method == "POST":
        plant_name = request.form["plant_name"]
        videos = get_plant_videos(plant_name)
    return render_template("index.html", videos=videos)

if __name__ == "__main__":
    app.run(debug=True)