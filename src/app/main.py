from fastapi import FastAPI, Request, Response, BackgroundTasks, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src.app.service import SpeedCameraService
import uvicorn
import os
import logging
import cv2

# Logging setup
log_dir = "data/logs"
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except Exception as e:
        print(f"Failed to create log directory: {e}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, "app.log"))
    ],
    force=True
)
logger = logging.getLogger("App")

app = FastAPI(title="Raspberry Pi Speed Camera")

# Session Middleware
app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key-in-production")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instance
service = SpeedCameraService()

# Application Version
APP_VERSION = "1.2.0 (GStreamer)"

# Mount static files
if not os.path.exists("src/frontend/static"):
    os.makedirs("src/frontend/static")
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

if not os.path.exists("src/frontend/templates"):
    os.makedirs("src/frontend/templates")
templates = Jinja2Templates(directory="src/frontend/templates")

# Serve captured images
if not os.path.exists("data/images"):
    os.makedirs("data/images")
app.mount("/images", StaticFiles(directory="data/images"), name="images")


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting Speed Camera Service... Version: {APP_VERSION}")
    # Wait a bit for camera init
    try:
        service.start()
    except Exception as e:
        logger.error(f"Failed to start service: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping Speed Camera Service...")
    service.stop()

# Auth Dependency
async def check_auth(request: Request):
    user = request.session.get("user")
    if not user:
        # For API calls, return 401
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Get credentials from config
    config_user = service.config.get("web", {}).get("username", "admin")
    config_pass = service.config.get("web", {}).get("password", "admin")
    
    if username == config_user and password == config_pass:
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/login")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if not request.session.get("user"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stream")
async def video_feed(request: Request):
    # Stream might be embedded in page, checking session here
    if not request.session.get("user"):
         raise HTTPException(status_code=401)
         
    def generate():
        while True:
            frame = service.get_jpeg_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                import time
                time.sleep(0.1)
                
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/config")
async def get_config(user: str = Depends(check_auth)):
    return service.config

@app.post("/api/config")
async def update_config(config: dict, user: str = Depends(check_auth)):
    success = service.save_config(config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save config")
    return {"status": "ok", "config": service.config}

@app.get("/api/history")
async def get_history(limit: int = 50, offset: int = 0, user: str = Depends(check_auth)):
    events = service.storage.get_events(limit, offset)
    return {"events": events}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
