# JEE CBT App — Render Ready

## Files
- app.py — Flask backend
- index.html — CBT frontend
- requirements.txt — Python dependencies
- render.yaml — Render deployment configuration

## Render
Create a Render Web Service from this project.

Build command:
pip install -r requirements.txt

Start command:
gunicorn app:app

The app listens on Render's assigned PORT through gunicorn.

## Homepage embedding
After deployment, embed the generated HTTPS URL:
<iframe src="YOUR_RENDER_URL" style="width:100%;height:900px;border:0"></iframe>

The app requires internet access for its online functionality.
