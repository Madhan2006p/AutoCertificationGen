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
    
    # Filter cleaning - exclude blocked participants
    clean_events = []
    for e in events:
        # Skip blocked participants
        if e.get("blocked") == 1:
            continue
        # Simplify display name
        if "CHILL" in e["event"].upper():
            d_name = "MINDSPRINT"
        else:
            d_name = e["event"].replace("MARKUS 2K26 - ", "").replace("(Responses)", "").strip()
        e["display_name"] = d_name
        clean_events.append(e)
        
    return templates.TemplateResponse("verify.html", {"request": request, "events": clean_events, "roll_no": roll_no})

@app.get("/generate_cert")
async def generate(request: Request, roll_no: str, event_id: str):
    from backend.database import is_participant_blocked
    
    # Sanitize inputs
    roll_no = roll_no.strip().upper()
    
    # Fetch record from DB
    events = get_events_for_roll(roll_no)
    record = next((e for e in events if e["event"] == event_id), None)
    
    if not record:
        # Fallback: Check if event_id is 'MINDSPRINT' but DB has 'CHILL & SKILL' or vice versa
        # This handles transitional state if DB Sync logic changed
        if event_id.upper() == "MINDSPRINT":
            record = next((e for e in events if "CHILL" in e["event"].upper()), None)
        elif "CHILL" in event_id.upper():
            record = next((e for e in events if e["event"] == "MINDSPRINT"), None)

    if not record:
        return HTMLResponse(f"Record not found for {roll_no} - {event_id}", status_code=404)
    
    # Check if blocked by admin
    if record.get("blocked") == 1 or is_participant_blocked(roll_no, event_id):
        return HTMLResponse("Certificate generation is disabled for this participant.", status_code=403)
        
    if record["cert_url"]:
        return RedirectResponse(record["cert_url"])
        
    # Generate certificate
    try:
        # Clean event name for display on certificate
        # Replace Chill and Skill with Mindsprint
        raw_event = record["event"]
        if "CHILL" in raw_event.upper() and "SKILL" in raw_event.upper():
            clean_event_name = "MINDSPRINT"
        elif "MINDSPRINT" in raw_event.upper():
            clean_event_name = "MINDSPRINT"
        else:
            clean_event_name = raw_event.replace("(Responses)", "").replace("MARKUS 2K26 - ", "").replace("MARKUS ", "").strip()
        
        local_path = generate_local_certificate(
            name=record["name"], 
            year=record["year"], 
            event=clean_event_name, 
            roll_no=roll_no,
            department=record.get("department", "")
        )
        
        # Upload to Cloudinary
        print(f"Uploading {local_path}...")
        res = cloudinary.uploader.upload(local_path, folder="markus_certs")
        url = res.get("secure_url")
        
        # Update DB with certificate URL
        update_cert_url(roll_no, event_id, url)
        
        return RedirectResponse(url)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"Error generating certificate: {e}", status_code=500)

@app.get("/sync")
async def manual_sync():
    """Admin endpoint to trigger sync"""
    threading.Thread(target=sync_data).start()
    return {"status": "Sync started in background"}

# ========== ADMIN PORTAL ==========
from backend.database import get_all_participants, toggle_cert_visibility, bulk_toggle_cert_visibility, get_stats

ADMIN_USERNAME = "Madhan2006p"
ADMIN_PASSWORD = "iamironman"
admin_sessions = set()

@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Simple session using cookie
        response = RedirectResponse("/admin/dashboard", status_code=302)
        response.set_cookie("admin_session", "authenticated", httponly=True, max_age=3600*8)
        return response
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid credentials"})

def is_admin(request: Request):
    return request.cookies.get("admin_session") == "authenticated"

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin/login", status_code=302)
    
    participants = get_all_participants()
    stats = get_stats()
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "participants": participants,
        "stats": stats
    })

@app.post("/admin/toggle/{participant_id}")
async def admin_toggle_cert(request: Request, participant_id: int, visible: bool = True):
    if not is_admin(request):
        return {"error": "Unauthorized"}, 401
    
    toggle_cert_visibility(participant_id, visible)
    return {"success": True, "visible": visible}

@app.post("/admin/toggle-all")
async def admin_toggle_all(request: Request, visible: bool = True):
    if not is_admin(request):
        return {"error": "Unauthorized"}, 401
    
    bulk_toggle_cert_visibility(visible)
    return {"success": True, "visible": visible}

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("admin_session")
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
