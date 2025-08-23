from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from waitress import serve

app = Flask(__name__)

# ======== CORS wala zaroori change ========
# Yahan apne Vercel ke saare possible URLs daalein
origins = [
    "https://parro.vercel.app",
    "https://parro-git-main-monubhai17s-projects.vercel.app",
    "https://parro-hvjmatx7-monubhai17s-projects.vercel.app" # Ye URL aapke error me dikha tha
]
CORS(app, resources={r"/process": {"origins": origins}})
# ==========================================

COLAB_URL = os.getenv("COLAB_URL", "").strip()

@app.route("/")
def home():
    return "<h1>Mithu-Backend is running!</h1>"

@app.get("/health")
def health():
    return {"ok": True, "colab_url_set": bool(COLAB_URL)}

@app.post("/process")
def process():
    # ... (baaki ka poora code waisa hi rahega) ...
    # ... (no changes needed here) ...
    pass # Placeholder

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
