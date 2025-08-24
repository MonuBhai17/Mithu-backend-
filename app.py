from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import requests
import json
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Colab configuration
COLAB_AUTH_TOKEN = "31Z9AgglFZPulkrMNenJ5FLA6j2_6hQcDDK4HVP66hHX4fc5V"
COLAB_NOTEBOOK_URL = "https://colab.research.google.com/drive/your_notebook_id"  # Replace with actual URL

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_job_id():
    return str(uuid.uuid4())

def trigger_colab_processing(job_id, main_video_path, reference_videos_paths):
    """Trigger Colab notebook for video processing"""
    try:
        # Prepare data for Colab
        payload = {
            "job_id": job_id,
            "main_video": main_video_path,
            "reference_videos": reference_videos_paths,
            "auth_token": COLAB_AUTH_TOKEN,
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would:
        # 1. Upload files to Google Drive or cloud storage
        # 2. Trigger Colab via webhook or API
        # 3. For now, we'll simulate the process
        
        logger.info(f"Processing job {job_id} with Colab")
        return {"status": "processing", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Error triggering Colab: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'main_video' not in request.files:
            return jsonify({"error": "Main video is required"}), 400
        
        main_video = request.files['main_video']
        reference_videos = request.files.getlist('reference_videos')
        
        if main_video.filename == '':
            return jsonify({"error": "No main video selected"}), 400
        
        if not allowed_file(main_video.filename):
            return jsonify({"error": "Invalid main video format"}), 400
        
        # Generate job ID
        job_id = generate_job_id()
        job_folder = os.path.join(UPLOAD_FOLDER, job_id)
        os.makedirs(job_folder, exist_ok=True)
        
        # Save main video
        main_filename = secure_filename(main_video.filename)
        main_video_path = os.path.join(job_folder, f"main_{main_filename}")
        main_video.save(main_video_path)
        
        # Save reference videos
        reference_paths = []
        for i, ref_video in enumerate(reference_videos):
            if ref_video.filename != '' and allowed_file(ref_video.filename):
                ref_filename = secure_filename(ref_video.filename)
                ref_path = os.path.join(job_folder, f"ref_{i}_{ref_filename}")
                ref_video.save(ref_path)
                reference_paths.append(ref_path)
        
        # Trigger Colab processing
        result = trigger_colab_processing(job_id, main_video_path, reference_paths)
        
        return jsonify({
            "job_id": job_id,
            "status": "uploaded",
            "main_video": main_video_path,
            "reference_videos": reference_paths,
            "processing_status": result["status"]
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/file/<filename>', methods=['GET'])
def serve_file(filename):
    """Serve uploaded files for Colab access"""
    try:
        # Find file in uploads directory
        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            if filename in files:
                file_path = os.path.join(root, filename)
                return send_file(file_path)
        
        return jsonify({"error": "File not found"}), 404
        
    except Exception as e:
        logger.error(f"File serve error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/register-webhook', methods=['POST'])
def register_webhook():
    """Register Colab webhook URL"""
    try:
        data = request.json
        if data.get('auth_token') != COLAB_AUTH_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        
        webhook_url = data.get('webhook_url')
        if webhook_url:
            # Store webhook URL (in production, save to database)
            global COLAB_WEBHOOK_URL
            COLAB_WEBHOOK_URL = webhook_url.replace('/process', '')  # Remove /process suffix
            
            logger.info(f"Registered Colab webhook: {COLAB_WEBHOOK_URL}")
            return jsonify({"status": "registered", "webhook_url": webhook_url})
        else:
            return jsonify({"error": "webhook_url required"}), 400
            
    except Exception as e:
        logger.error(f"Webhook registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/upload-result', methods=['POST'])
def upload_result():
    """Receive processed video from Colab"""
    try:
        # Verify auth token
        auth_token = request.form.get('auth_token')
        if auth_token != COLAB_AUTH_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        
        job_id = request.form.get('job_id')
        video_file = request.files.get('video')
        
        if not job_id or not video_file:
            return jsonify({"error": "job_id and video file required"}), 400
        
        # Save the processed video
        output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}_output.mp4")
        video_file.save(output_path)
        
        # Update job status
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = "completed"
            active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            active_jobs[job_id]["output_path"] = output_path
        
        download_url = f"/download/{job_id}"
        
        logger.info(f"Received processed video for job {job_id}")
        return jsonify({
            "status": "success",
            "job_id": job_id,
            "download_url": download_url
        })
        
    except Exception as e:
        logger.error(f"Upload result error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/job-status', methods=['POST'])
def update_job_status():
    """Receive job status updates from Colab"""
    try:
        data = request.json
        if data.get('auth_token') != COLAB_AUTH_TOKEN:
            return jsonify({"error": "Unauthorized"}), 401
        
        job_id = data.get('job_id')
        status = data.get('status')
        message = data.get('message')
        
        if job_id in active_jobs:
            active_jobs[job_id]["status"] = status
            active_jobs[job_id]["last_update"] = datetime.now().isoformat()
            if message:
                active_jobs[job_id]["message"] = message
        
        logger.info(f"Job {job_id} status updated: {status}")
        return jsonify({"status": "updated"})
        
    except Exception as e:
        logger.error(f"Status update error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    try:
        output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}_output.mp4")
        
        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, download_name=f"shorts_{job_id}.mp4")
        else:
            return jsonify({"error": "Video not ready or not found"}), 404
            
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/jobs', methods=['GET'])
def list_jobs():
    try:
        jobs = []
        if os.path.exists(UPLOAD_FOLDER):
            for job_id in os.listdir(UPLOAD_FOLDER):
                if os.path.isdir(os.path.join(UPLOAD_FOLDER, job_id)):
                    output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}_output.mp4")
                    status = "completed" if os.path.exists(output_path) else "processing"
                    jobs.append({"job_id": job_id, "status": status})
        
        return jsonify({"jobs": jobs})
        
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 500MB"}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
