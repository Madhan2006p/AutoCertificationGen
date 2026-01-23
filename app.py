from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import threading
import cloudinary
import cloudinary.uploader
from backend.database import get_events_for_roll, update_cert_url, init_db
from backend.certificate import generate_local_certificate
from backend.sync import sync_data

app = FastAPI()

# Config
templates = Jinja2Templates(directory="templates")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Startup
@app.on_event("startup")
def startup():
    if not os.path.exists("backend/generated"):
        os.makedirs("backend/generated")
    init_db()
    # Optional: Auto-sync on startup (can slow down boot, but good for MVP)
    # threading.Thread(target=sync_data).start()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/verify", response_class=HTMLResponse)
async def verify(request: Request, roll_no: str = Form(...)):
    roll_no = roll_no.strip().upper()
    events = get_events_for_roll(roll_no)
    
    # Filter cleaning
    clean_events = []
    for e in events:
        # Simplify display name
        d_name = e["event"].replace("MARKUS 2K26 - ", "").replace("(Responses)", "").strip()
        e["display_name"] = d_name
        clean_events.append(e)
        
    return templates.TemplateResponse("verify.html", {"request": request, "events": clean_events, "roll_no": roll_no})

@app.get("/generate/{roll_no}/{event_id}")
async def generate(request: Request, roll_no: str, event_id: str): # Using event name as ID for now
    # Security/Validation needed?
    # Logic: 
    # 1. Check if cert_url exists in DB
    # 2. If yes, redirect
    # 3. If no, generate, upload, save, redirect
    
    # We need to fetch full record to get Name/Year
    events = get_events_for_roll(roll_no)
    record = next((e for e in events if e["event"] == event_id), None)
    
    if not record:
        return HTMLResponse("Record not found", status_code=404)
        
    if record["cert_url"]:
        return RedirectResponse(record["cert_url"])
        
    # Generate
    try:
        local_path = generate_local_certificate(record["name"], record["year"], record["display_name"], roll_no) # Use display name on cert? Or official?
        # User said "Event: (1301, 294)". Usually official name is too long.
        # Let's use the full name from DB "event" but maybe strip " (Responses)"
        clean_event_name = record["event"].replace("(Responses)", "").replace("MARKUS 2K26 - ", "").strip()
        
        # Regenerate with clean name
        local_path = generate_local_certificate(record["name"], record["year"], clean_event_name, roll_no)
        
        # Upload
        print(f"Uploading {local_path}...")
        res = cloudinary.uploader.upload(local_path, folder="markus_certs")
        url = res.get("secure_url")
        
        # Update DB
        update_cert_url(roll_no, event_id, url)
        
        return RedirectResponse(url)
        
    except Exception as e:
        print(f"Error: {e}")
        return HTMLResponse(f"Error generating certificate: {e}", status_code=500)

@app.get("/sync")
async def manual_sync():
    """Admin endpoint to trigger sync"""
    threading.Thread(target=sync_data).start()
    return {"status": "Sync started in background"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
