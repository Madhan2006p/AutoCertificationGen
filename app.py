from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend import access_person as ap
from backend import admin_analytics
import os
import uvicorn
import cloudinary
import cloudinary.uploader
import sqlite3
import time
import hashlib
import secrets
from tasks import generate_and_upload_cert

# ============================================
# ADMIN CREDENTIALS (Hardcoded as requested)
# ============================================
ADMIN_USERNAME = "Madhan2006p"
ADMIN_PASSWORD = "iamironman"

# Simple session storage (in-memory for simplicity)
# In production, use Redis or database sessions
admin_sessions = {}

def generate_session_token():
    return secrets.token_hex(32)

def verify_admin_session(request: Request) -> bool:
    """Verify if the request has a valid admin session."""
    session_token = request.cookies.get("admin_session")
    return session_token and session_token in admin_sessions

# Helper to check maintenance mode
def is_maintenance():
    try:
        conn = sqlite3.connect("forms_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key='maintenance'")
        res = cursor.fetchone()
        conn.close()
        return res and res[0] == "true"
    except Exception:
        return False

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    # Allow admin routes and health checks even in maintenance
    if is_maintenance() and not request.url.path.startswith("/admin") and request.url.path != "/status":
        return JSONResponse(
            status_code=503,
            content={"message": "Certificate portal is under maintenance for data syncing. Try again in 10 minutes."}
        )
    return await call_next(request)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory="templates")

# Cloudinary Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

@app.get("/", response_class=HTMLResponse)
@limiter.limit("10/minute")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/verify", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def verify(request: Request, roll: str = None):
    if not roll:
        return HTMLResponse(content="Invalid QR code", status_code=400)

    roll = roll.lower()
    data = ap.get_user_by_reg(roll)

    if data.empty:
        return templates.TemplateResponse("verify.html", {"request": request, "status": "invalid"})

    return templates.TemplateResponse(
        "verify.html",
        {
            "request": request,
            "status": "valid",
            "roll": roll,
            "records": data.to_dict(orient="records")
        }
    )

@app.get("/download")
@limiter.limit("3/minute")
async def download(request: Request, roll: str, event: str):
    """
    Production-safe download logic with RACE CONDITION protection.
    """
    roll = roll.lower()
    data = ap.get_user_by_reg(roll)
    
    if data.empty:
        raise HTTPException(status_code=404, detail="User not eligible or not found.")
    
    records = data.to_dict(orient="records")
    user_record = next((r for r in records if r['event'] == event), None)
    
    if not user_record:
        raise HTTPException(status_code=404, detail="Participation record not found for this event.")

    cert_url = user_record.get("cert_url")

    # 1. Instant Redirect if already exists
    if cert_url:
        return RedirectResponse(cert_url)
    
    # 2. Prevent Race Condition: Atomically claim the generation
    conn = sqlite3.connect("forms_data.db", timeout=10)
    cursor = conn.cursor()
    
    # Try to claim the "generating" status
    # Only succeeds if cert_url is still NULL and generating is 0
    cursor.execute("""
        UPDATE participants 
        SET generating = 1 
        WHERE roll_no = ? AND event = ? AND (cert_url IS NULL OR cert_url = '') AND generating = 0
    """, (roll, event))
    
    claimed = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if claimed:
        # We are the winner of the race. Generate and upload.
        print(f"🚀 [INIT] Generating for {roll} - {event} (Race Winner)")
        try:
            new_url = generate_and_upload_cert(
                roll_no=roll, 
                name=user_record['name'], 
                event=event, 
                year=user_record['year']
            )
            return RedirectResponse(new_url)
        finally:
            # Important: Reset generating flag even if it failed (so retry works)
            conn = sqlite3.connect("forms_data.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE participants SET generating = 0 WHERE roll_no = ? AND event = ?", (roll, event))
            conn.commit()
            conn.close()
    else:
        # Someone else is already generating it. Wait and check.
        print(f"⏳ [WAIT] {roll} is already being generated by another request. Waiting...")
        for _ in range(15): # wait up to 15 seconds
            time.sleep(1)
            data = ap.get_user_by_reg(roll)
            user_record = next((r for r in data.to_dict(orient="records") if r['event'] == event), None)
            if user_record and user_record.get("cert_url"):
                return RedirectResponse(user_record["cert_url"])
        
        raise HTTPException(status_code=429, detail="Generation in progress. Please refresh in a few seconds.")


# ============================================
# ADMIN ROUTES
# ============================================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Display the admin login page."""
    # If already logged in, redirect to dashboard
    if verify_admin_session(request):
        return RedirectResponse("/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login form submission."""
    # Verify credentials
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Create session token
        session_token = generate_session_token()
        admin_sessions[session_token] = {
            "username": username,
            "login_time": time.time()
        }
        
        # Create redirect response with session cookie
        response = RedirectResponse("/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            httponly=True,
            max_age=3600 * 8,  # 8 hours
            samesite="lax"
        )
        
        print(f"🔐 Admin login successful: {username}")
        return response
    
    # Invalid credentials
    print(f"❌ Admin login failed: {username}")
    return templates.TemplateResponse(
        "admin_login.html", 
        {"request": request, "error": "Invalid username or password"}
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Display the admin dashboard with comprehensive analytics."""
    # Check if logged in
    if not verify_admin_session(request):
        return RedirectResponse("/admin/login", status_code=302)
    
    # Fetch analytics data
    analytics = admin_analytics.fetch_admin_analytics()
    
    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            # Basic stats
            "total_unique": analytics["total_unique"],
            "total_responses": analytics["total_responses"],
            "dept_count": analytics["dept_count"],
            # Event data
            "events": analytics["events"],
            # Department breakdown
            "departments": analytics["departments"],
            # Multi-event participation
            "participation_breakdown": analytics["participation_breakdown"],
            "multi_event_participants": analytics["multi_event_participants"],
            "popular_combos": analytics["popular_combos"],
            # Engagement metrics
            "engagement": analytics["engagement"],
            # Metadata
            "refresh_time": analytics["refresh_time"]
        }
    )

@app.get("/admin/logout")
async def admin_logout(request: Request):
    """Log out the admin user."""
    session_token = request.cookies.get("admin_session")
    
    if session_token and session_token in admin_sessions:
        del admin_sessions[session_token]
        print("🚪 Admin logged out")
    
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("admin_session")
    return response

@app.get("/admin/api/analytics")
async def admin_api_analytics(request: Request):
    """API endpoint to get analytics data (JSON)."""
    if not verify_admin_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return admin_analytics.fetch_admin_analytics()


# --- Admin Controls ---

@app.get("/admin/maintenance/{state}")
async def toggle_maintenance(request: Request, state: str):
    # Require admin login for maintenance toggle
    if not verify_admin_session(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if state not in ["true", "false"]:
        return {"error": "Invalid state"}
    
    conn = sqlite3.connect("forms_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'maintenance'", (state,))
    conn.commit()
    conn.close()
    return {"maintenance": state}

# Simple status endpoint
@app.get("/status")
async def status():
    return {"status": "ok", "message": "Mark-us 26 Certificate Portal is ready!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Note: reload=True for development only
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)