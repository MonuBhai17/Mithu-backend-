from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from waitress import serve

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

COLAB_URL = os.getenv("COLAB_URL", "").strip()

@app.route("/")
def home():
    return "<h1>Mithu-Backend is running!</h1>"

@app.post("/process")
def process():
    if not COLAB_URL:
        return jsonify({"error": "COLAB_URL not set in Replit Secrets"}), 500

    video_file = request.files.get("video_file")
    video_url = request.form.get("video_url")
    
    if not video_file and not video_url:
        return jsonify({"error": "Video source is required"}), 400

    # Data ko aage Colab ko bhejna hai
    colab_payload = request.form.to_dict()
    colab_files = {'video_file': (video_file.filename, video_file.stream, video_file.mimetype)} if video_file else {}

    try:
        resp = requests.post(
            COLAB_URL,
            data=colab_payload,
            files=colab_files,
            timeout=300
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
