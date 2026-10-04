import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from pakka_hal.config import city_config, PORT, HOST, ENVIRONMENT
from pakka_hal.api.open311_routes import router as open311_router
from pakka_hal.api.pakka_routes import router as pakka_router
from pakka_hal.storage.db import init_db

app = FastAPI(
    title="Pakka Hal: Verified-Resolution Rails for Chandigarh",
    description="Digital Public Infrastructure (DPI) accountability and verified-resolution layer for civic services. Open311 GeoReport v2 compatible with evidence-based closure verification, Indic voice intake, and tamper-evident SHA-256 public ledger.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Mount APIs
app.include_router(open311_router)
app.include_router(pakka_router)

# Ensure static directory exists
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "city": city_config.get("city", {}).get("name", "Chandigarh"),
        "environment": ENVIRONMENT,
        "standard": "Open311 GeoReport v2 + Pakka Hal DPI Extensions",
        "ledger": "SHA-256 Hash Chain Active"
    }

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Pakka Hal API Running. See <a href='/docs'>/docs</a></h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
