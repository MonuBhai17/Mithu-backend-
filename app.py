from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import requests
import tempfile
import uuid
from werkzeug.utils import secure_filename
import json
import time

app = Flask(__name__)
CORS(app)

# Configuration
COLAB_NGROK_URL = os.environ.get('COLAB_NGROK_URL', 'https://your-ngrok-url.ngrok.io')
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return jsonify({
        "message": "AI Video Editor API",
        "status": "running",
        "endpoints": {
            "upload": "/upload",
            "process": "/process",
            "status": "/status/<job_id>",
            "download": "/download/<job_id>"
        }
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        reference_urls = request.form.get('reference_urls', '').split(',')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            filename = secure_filename(file.filename)
            
            # Save uploaded file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
            file.save(file_path)
            
            return jsonify({
                'job_id': job_id,
                'filename': filename,
                'file_path': file_path,
                'reference_urls': [url.strip() for url in reference_urls if url.strip()],
                'message': 'File uploaded successfully'
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        file_path = data.get('file_path')
        reference_urls = data.get('reference_urls', [])
        
        if not job_id or not file_path:
            return jsonify({'error': 'Missing job_id or file_path'}), 400
        
        # Send processing request to Colab
        colab_payload = {
            'job_id': job_id,
            'video_path': file_path,
            'reference_urls': reference_urls,
            'output_duration': 60  # 60 seconds
        }
        
        # Forward request to Colab ngrok endpoint
        colab_response = requests.post(
            f"{COLAB_NGROK_URL}/process_video",
            json=colab_payload,
            timeout=300  # 5 minutes timeout
        )
        
        if colab_response.status_code == 200:
            result = colab_response.json()
            return jsonify({
                'job_id': job_id,
                'status': 'processing',
                'message': 'Video processing started',
                'colab_response': result
            })
        else:
            return jsonify({
                'error': 'Failed to start processing',
                'colab_error': colab_response.text
            }), 500
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Colab connection error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    try:
        # Check status from Colab
        response = requests.get(f"{COLAB_NGROK_URL}/status/{job_id}", timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return jsonify({'error': 'Failed to get status'}), 500
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Colab connection error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    try:
        # Get processed video from Colab
        response = requests.get(f"{COLAB_NGROK_URL}/download/{job_id}", stream=True, timeout=60)
        
        if response.status_code == 200:
            # Save the processed video locally
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{job_id}_processed.mp4")
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return send_file(output_path, as_attachment=True, download_name=f"processed_{job_id}.mp4")
        else:
            return jsonify({'error': 'Processed video not found'}), 404
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Colab connection error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check if Colab is accessible
        colab_status = requests.get(f"{COLAB_NGROK_URL}/health", timeout=10)
        colab_healthy = colab_status.status_code == 200
    except:
        colab_healthy = False
    
    return jsonify({
        'render_status': 'healthy',
        'colab_status': 'healthy' if colab_healthy else 'unhealthy',
        'colab_url': COLAB_NGROK_URL
    })

@app.route('/update_colab_url', methods=['POST'])
def update_colab_url():
    global COLAB_NGROK_URL
    data = request.get_json()
    new_url = data.get('url')
    
    if new_url:
        COLAB_NGROK_URL = new_url
        return jsonify({'message': f'Colab URL updated to {new_url}'})
    
    return jsonify({'error': 'No URL provided'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
