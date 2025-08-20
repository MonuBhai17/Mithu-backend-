# MITHU.AI Backend (Flask) — Colab Connected

## How it works
Frontend -> **/process** (Flask) -> forwards to **Colab /process** -> heavy processing -> JSON back.

## Quick Start (Replit - Phone)
1. New Python Repl → Add files from this repo.
2. Shell: `pip install -r requirements.txt`
3. Add Secret: `COLAB_URL = https://<your-ngrok>.ngrok-free.app/process`
4. Run → open `/health` (should show `{ ok: true }`).

## API
- `GET /health`
- `POST /process`  
  ```json
  {"video_url":"<http/drive url>", "reference_url":"<youtube shorts url>"}
