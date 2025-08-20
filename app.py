from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ COLAB_URL Replit Secrets se uthana
COLAB_URL = os.getenv("COLAB_URL", "").strip()

@app.get("/health")
def health():
    """
    Health check endpoint
    """
    return {
        "ok": True,
        "colab_url_set": bool(COLAB_URL),
        "colab_url": COLAB_URL if COLAB_URL else None
    }

@app.post("/process")
def process():
    """
    Flow: Frontend -> Replit Flask -> Colab
    Request JSON: {"video_url": "...", "reference_url": "..."}
    Response JSON (from Colab expected):
    {"status": "success", "result_url": "https://.../final.mp4"}
    """
    data = request.get_json(force=True, silent=True) or {}
    video_url = data.get("video_url")
    reference_url = data.get("reference_url")

    # Validation
    if not video_url or not reference_url:
        return {"error": "video_url and reference_url required"}, 400

    if not COLAB_URL:
        return {"error": "COLAB_URL not set in Replit Secrets"}, 500

    try:
        resp = requests.post(
            COLAB_URL,
            json={"video_url": video_url, "reference_url": reference_url},
            timeout=180
        )
        # Forward response from Colab
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.Timeout:
        return {"error": "Colab server timed out"}, 504
    except Exception as e:
        return {"error": f"failed to reach Colab: {str(e)}"}, 502


if __name__ == "__main__":
    # Replit assigns PORT automatically; fallback 8080
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
