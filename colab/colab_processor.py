# Run this cell in Google Colab to expose /process endpoint publicly.
# Steps (single cell):
# 1) pip install
# 2) start flask
# 3) expose via ngrok
# 4) implement simple 60s trim using moviepy (optional demo)

import subprocess, sys, json, os, threading
from flask import Flask, request, jsonify

# ---- install deps ----
!pip -q install flask pyngrok moviepy requests >/dev/null

from pyngrok import ngrok
from moviepy.editor import VideoFileClip
import requests

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json(force=True, silent=True) or {}
    video_url = data.get("video_url")
    reference_url = data.get("reference_url")

    if not video_url or not reference_url:
        return jsonify({"error": "video_url and reference_url required"}), 400

    in_path = "/content/input.mp4"
    out_path = "/content/output_60s.mp4"

    try:
        # download input
        r = requests.get(video_url, stream=True, timeout=120)
        r.raise_for_status()
        with open(in_path, "wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)

        # trim to <= 60 sec (demo)
        clip = VideoFileClip(in_path)
        end_s = min(60, int(clip.duration))
        sub = clip.subclip(0, end_s)
        sub.write_videofile(out_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
        clip.close()

        # TODO: Upload out_path to your cloud (Firebase/Drive) and get public URL.
        # For demo, we return a local placeholder URL.
        # Replace below with your uploader and set real public link:
        result_url = "https://example.com/final_video.mp4"

        return jsonify({"status": "success", "result_url": result_url})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---- expose ----
public_url = ngrok.connect(5000, bind_tls=True).public_url
print("Public Colab URL:", public_url)
print("Set this in backend as COLAB_URL:", public_url + "/process")

def run():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run, daemon=True).start()
