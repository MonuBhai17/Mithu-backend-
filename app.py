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
    # Naya tareeka: Seedha JSON recieve karna
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    video_url = data.get('video_url')
    reference_url = data.get('reference_url')

    if not video_url or not reference_url:
        return jsonify({"error": "video_url and reference_url are required"}), 400
    
    # Colab ko aage JSON hi bhejenge
    colab_payload = {
        "video_url": video_url,
        "reference_url": reference_url
    }

    try:
        resp = requests.post(COLAB_URL, json=colab_payload, timeout=300)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
