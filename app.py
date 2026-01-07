from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job
from backend import access_person as ap
import os
import uvicorn
from tasks import long_task

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Redis Connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_conn = Redis.from_url(redis_url)
    queue = Queue("default", connection=redis_conn)
except Exception as e:
    print(f"Warning: Could not connect to Redis: {e}")
    queue = None

class JobRequest(BaseModel):
    data: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/verify", response_class=HTMLResponse)
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
async def download(roll: str, event: str):
    path = f"backend/certificates/{roll}_{event.replace(' ', '_')}.png"
    return FileResponse(path, filename=f"{roll}_{event}.png")

# --- Architecture Implementation Endpoints ---

@app.post("/api/process")
async def process(job_request: JobRequest):
    if not queue:
         raise HTTPException(status_code=503, detail="Redis queue not available")
    
    # Enqueue the job. We pass the function reference and arguments.
    job = queue.enqueue(long_task, job_request.data)
    
    return {
        "job_id": job.id,
        "status": "queued",
        "data_received": job_request.data
    }

@app.get("/api/status/{job_id}")
async def job_status(job_id: str):
    if not queue:
         raise HTTPException(status_code=503, detail="Redis queue not available")
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "result": job.result
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Reload=True is good for dev, but might duplicate workers if not careful.
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)