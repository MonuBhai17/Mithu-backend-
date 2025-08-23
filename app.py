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

@app.get("/health")
def health():
    return {"ok": True, "colab_url_set": bool(COLAB_URL)}

# ===== PROCESS FUNCTION ME JAASOOSI CODE DAALA GAYA HAI =====
@app.post("/process")
def process():
    # Jaasoos (Detective) Code:
    print("--- REQUEST HEADERS ---")
    print(request.headers)
    print("--- REQUEST DATA (RAW) ---")
    print(request.get_data())
    print("-----------------------")

    # Isse humein पता chalega ki frontend se kya data aa raha hai.
    # Abhi ke liye hum aage process nahi karenge.
    
    # Check karke dekhte hain ki 'form' available hai ya nahi
    if not hasattr(request, 'form'):
        print("ERROR: request.form available nahi hai!")
    else:
        print("SUCCESS: request.form available hai!")
        print(request.form)

    return jsonify({"status": "debug_check_logs"})

if __name__ == "__main__":
    print("Starting server with waitress...")
    serve(app, host="0.0.0.0", port=8080)
