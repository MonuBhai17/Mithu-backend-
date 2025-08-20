from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Set this in Replit (Secrets) or environment:
# Example: https://<your-ngrok>.ngrok-free.app/process
COLAB_URL = os.getenv("COLAB_URL", "").strip()

@app.get("/health")
def health():
    return {"ok": True, "colab_url_set": bool(COLAB_URL)}

@app.post("/process")
def process():
    """
    Frontend -> (video_url, reference_url) -> Flask -> Colab
    Colab will do heavy processing and return a JSON like:
    {"status": "success", "result_url": "https://.../final.mp4"}
    """
    data = request.get_json(force=True, silent=True) or {}
    video_url = data.get("video_url")
    reference_url = data.get("reference_url")

    if not video_url or not reference_url:
        return {"error": "video_url and reference_url required"}, 400

    if not COLAB_URL:
        return {"error": "COLAB_URL not set in env"}, 500

    try:
        resp = requests.post(
            COLAB_URL,
            json={"video_url": video_url, "reference_url": reference_url},
            timeout=180
        )
        # Forward Colab response as-is
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return {"error": f"failed to reach colab: {e}"}, 502


if __name__ == "__main__":
    # Replit usually maps PORT env; default 8080 for consistency
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
