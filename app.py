from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from waitress import serve
import uuid

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# In-memory storage (simple version)
colab_workers = {}
jobs = {}

# Frontend se request lene ke liye endpoint
@app.post("/process")
def process_from_frontend():
    if not colab_workers:
        return jsonify({"error": "No Colab worker is currently available."}), 503

    active_colab_url = list(colab_workers.values())[0]['webhook_url']
    frontend_data = request.json
    job_id = str(uuid.uuid4())
    
    colab_payload = {
        "job_id": job_id,
        "main_video_url": frontend_data.get("video_url"),
        "reference_video_urls": [frontend_data.get("reference_url")],
        "auth_token": os.getenv("COLAB_AUTH_TOKEN")
    }
    
    jobs[job_id] = {"status": "sent_to_colab", "result_url": None}
    
    try:
        requests.post(active_colab_url, json=colab_payload, timeout=10)
        return jsonify({"status": "processing_started", "job_id": job_id})
    except Exception as e:
        return jsonify({"error": "Failed to send job to Colab worker"}), 500

# Colab se register karne ke liye endpoint
@app.post("/register-webhook")
def register_webhook():
    data = request.json
    worker_url = data.get("webhook_url")
    if worker_url:
        colab_workers[worker_url] = data
        return jsonify({"status": "webhook_registered", "url": worker_url})
    return jsonify({"error": "Invalid registration data"}), 400

# Colab se result recieve karne ke liye endpoint
@app.post("/upload-result")
def upload_result():
    job_id = request.form.get('job_id')
    video_file = request.files.get('video')
    
    if job_id and video_file:
        # Yahan file ko cloud storage par save karna chahiye
        download_url = f"https://your-storage.com/{video_file.filename}"
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['result_url'] = download_url
        return jsonify({"status": "result_uploaded", "download_url": download_url})
    return jsonify({"error": "Invalid upload data"}), 400

# Colab se status update lene ke liye endpoint
@app.post("/job-status")
def job_status():
    data = request.json
    job_id = data.get('job_id')
    status = data.get('status')
    if job_id and status:
        if job_id in jobs:
            jobs[job_id]['status'] = status
            if status == 'completed':
                 jobs[job_id]['result_url'] = data.get('download_url')
        return jsonify({"status": "notification_received"})
    return jsonify({"error": "Invalid status data"}), 400

# Frontend ko job ka status batane ke liye endpoint
@app.get("/get-job-status/<job_id>")
def get_job_status(job_id):
    job = jobs.get(job_id)
    if job:
        return jsonify(job)
    return jsonify({"error": "Job not found"}), 404

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
