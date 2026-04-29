from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_app_password'     # Replace with your app password
mail = Mail(app)

# API Config
API_KEY = 'your_plant_id_api_key'
API_URL = 'https://plant.id/api/v3/identification'
WIKIPEDIA_API_URL = 'https://en.wikipedia.org/w/api.php'
GBIF_API_URL = "https://api.gbif.org/v1/species/match"
DETAILS_URL = "https://api.gbif.org/v1/species/{}"
YOUTUBE_API_KEY = "your_youtube_api_key"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Scheduler for Email Reminders
scheduler = BackgroundScheduler()

# SQLite DB init
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            watering_time TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Reminder Function
def send_reminders():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT name, email FROM users")
    users = c.fetchall()
    for name, email in users:
        msg = Message("Plant Watering Reminder", recipients=[email])
        msg.body = f"Hi {name},\n\nDon't forget to water your plants today!\n\n- PlantMate 🌱"
        mail.send(msg)
    conn.close()

scheduler.add_job(send_reminders, 'interval', hours=24)
scheduler.start()

# Wikipedia

def get_plant_details_wikipedia(plant_name):
    try:
        params = {
            'action': 'query',
            'format': 'json',
            'titles': plant_name,
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
        }
        response = requests.get(WIKIPEDIA_API_URL, params=params)
        pages = response.json().get('query', {}).get('pages', {})
        for _, page_data in pages.items():
            return page_data.get('extract', 'No details found.')
    except:
        return "No details found."

# GBIF

def get_plant_details(plant_name):
    try:
        response = requests.get(GBIF_API_URL, params={"name": plant_name, "verbose": "true"})
        data = response.json()
        if "scientificName" in data:
            species_key = data.get("usageKey", "N/A")
            details = {
                "Scientific Name": data.get("scientificName", "N/A"),
                "Kingdom": data.get("kingdom", "N/A"),
                "Phylum": data.get("phylum", "N/A"),
                "Class": data.get("class", "N/A"),
                "Order": data.get("order", "N/A"),
                "Family": data.get("family", "N/A"),
                "Genus": data.get("genus", "N/A"),
                "More Info": f"https://www.gbif.org/species/{species_key}"
            }
            if species_key != "N/A":
                common_name_response = requests.get(DETAILS_URL.format(species_key))
                if common_name_response.status_code == 200:
                    common_name = common_name_response.json().get("vernacularName", "N/A")
                    details["Common Name"] = common_name
            return details
    except:
        return {"Error": "No plant found."}

# YouTube Videos

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

# Routes

@app.route("/")
def home():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/identify", methods=["POST"])
def identify():
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        with open(file_path, "rb") as image_file:
            files = {"images": image_file}
            headers = {"Api-Key": API_KEY}
            response = requests.post(API_URL, files=files, headers=headers)
        if response.status_code == 201:
            result = response.json()
            suggestions = result.get("result", {}).get("classification", {}).get("suggestions", [])
            top_suggestion = suggestions[0].get("name", "Unknown") if suggestions else "Unknown"
            probability = float(suggestions[0].get("probability", 0)) if suggestions else 0
            return redirect(url_for("result", image=file.filename, plant_name=top_suggestion, probability=probability))
    return "Error identifying plant."

@app.route("/result")
def result():
    image = request.args.get("image")
    plant_name = request.args.get("plant_name")
    probability = round(float(request.args.get("probability", 0)) * 100, 2)
    image_url = os.path.join("static/uploads", image) if image else None
    return render_template("result.html", image_url=image_url, plant_name=plant_name, probability=probability)

@app.route("/plant-details")
def plant_details():
    plant_name = request.args.get('plant_name', 'Unknown')
    details = get_plant_details(plant_name)
    wiki_details = get_plant_details_wikipedia(plant_name)
    return render_template("plantdetails.html", plant_name=plant_name, details=details, wiki_details=wiki_details)

@app.route("/videos")
def videos():
    plant_name = request.args.get("plant_name", "Unknown")
    details = get_plant_details(plant_name)
    videos = get_plant_videos(details.get("Common Name", plant_name))
    return render_template("videos.html", videos=videos)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["email"] = user[2]
            session["name"] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        watering_time = request.form["watering_time"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, password, watering_time) VALUES (?, ?, ?, ?)",
                      (name, email, password, watering_time))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "warning")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)