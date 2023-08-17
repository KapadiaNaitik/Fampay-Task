from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from flask import Flask, request, jsonify
import requests
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect
from dotenv import load_dotenv
import os


app = Flask(__name__)


# Load environment variables from .env file
load_dotenv()

API_KEYS = os.getenv("API_KEYS").split(",")
SEARCH_QUERY = os.getenv("SEARCH_QUERY")
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL"))
MAX_RESULTS_PER_PAGE = int(os.getenv("MAX_RESULTS_PER_PAGE"))


DATA_STORE = []
DATA_LOCK = threading.Lock()
KEY_INDEX = 0  # Index for a simple round robin style algorithm
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
db = SQLAlchemy(app)


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    thumbnail_url = db.Column(db.String(255))


@app.cli.command("initdb")
def init_db():
    with app.app_context():
        db.create_all()
    print("Database created.")


def fetch_videos():
    global KEY_INDEX
    while True:
        api_key = API_KEYS[KEY_INDEX]
        url = f'https://www.googleapis.com/youtube/v3/search?type=video&order=date&publishedAfter=2023-08-01T00:00:00Z&q={SEARCH_QUERY}&key={api_key}&maxResults={MAX_RESULTS_PER_PAGE}'
        response = requests.get(url)
        print(response)
        if response.status_code == 200:
            search_results = response.json().get('items', [])
            video_ids = [result['id']['videoId'] for result in search_results]

            # Fetch video details for the obtained video ids.
            videos = []
            for video_id in video_ids:
                video_url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={api_key}&part=snippet'
                video_response = requests.get(video_url)
                if video_response.status_code == 200:
                    video_data = video_response.json().get('items', [])[0]
                    videos.append(video_data)
            print(videos)

            # Stored the details in database
            with app.app_context():
                for video in videos:
                    published_at_str = video['snippet']['publishedAt']
                    published_at = datetime.strptime(
                        published_at_str, '%Y-%m-%dT%H:%M:%SZ')
                    new_video = Video(
                        title=video['snippet']['title'],
                        description=video['snippet']['description'],
                        published_at=published_at,
                        thumbnail_url=video['snippet']['thumbnails']['default']['url']
                    )
                    db.session.add(new_video)
                db.session.commit()
        else:
            print(
                f"API request failed with status code {response.status_code}")

        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        time.sleep(REFRESH_INTERVAL)


thread = threading.Thread(target=fetch_videos)
thread.daemon = True
thread.start()

# API route for paginated video data


@app.route('/videos', methods=['GET'])
def get_videos():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    start = (page - 1) * per_page
    end = start + per_page

    with DATA_LOCK:
        sorted_data = sorted(
            DATA_STORE, key=lambda x: x['snippet']['publishedAt'], reverse=True)
        paginated_data = sorted_data[start:end]

    return jsonify(paginated_data)

# API route for updataing search query initial is grabbed from environment variable


@app.route('/update_search_query', methods=['POST'])
def update_search_query():
    new_search_query = request.form.get('search_query')
    global SEARCH_QUERY
    SEARCH_QUERY = new_search_query
    return redirect('/dashboard')

# API route to render dashboard


@app.route('/dashboard', methods=['GET'])
def dashboard():
    videos = Video.query.order_by(Video.published_at.desc()).all()
    return render_template('dashboard.html', videos=videos)

# API route to sort videos


@app.route('/sort_videos', methods=['GET'])
def sort_videos():
    sort_option = request.args.get('sort_by', 'published_at_desc')

    with app.app_context():
        if sort_option == 'published_at_desc':
            sorted_videos = Video.query.order_by(
                Video.published_at.desc()).all()
        elif sort_option == 'published_at_asc':
            sorted_videos = Video.query.order_by(
                Video.published_at.asc()).all()
        elif sort_option == 'title_asc':
            sorted_videos = Video.query.order_by(
                Video.title.asc()).all()
        elif sort_option == 'title_desc':
            sorted_videos = Video.query.order_by(
                Video.title.desc()).all()
        else:
            sorted_videos = Video.query.all()

    return render_template('dashboard.html', videos=sorted_videos)


if __name__ == '__main__':
    app.run(debug=True)
