from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from backend import access_person as ap
import os
import uvicorn

app = FastAPI()

templates = Jinja2Templates(directory="templates")

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
    # Ensure event is string to avoid issues, though type hint enforces it mostly
    path = f"backend/certificates/{roll}_{event.replace(' ', '_')}.png"
    
    # send_file(as_attachment=True) equivalent is filename argument in FileResponse
    return FileResponse(path, filename=f"{roll}_{event}.png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)