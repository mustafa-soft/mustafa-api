from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Mustafa Soft API",
    description="API for mustafa-soft.com - GSM Tools Store",
    version="1.0.0"
)

# Allow all origins for your store
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MAIN ROUTE - ده المهم لـ Galle =====
@app.get("/")
def home():
    return {
        "status": "Running",
        "message": "Server is running successfully!",
        "store": "mustafa-soft.com",
        "new_store": "gsm.mustafa-soft.com",
        "galle_connected": True,
        "tools_live": 15,
        "email_galle": "mustafaopen88@gmail.com",
        "api_version": "1.0"
    }

@app.get("/status")
def status():
    return {
        "status": "Running",
        "galle_connected": True,
        "galle_email": "mustafaopen88@gmail.com",
        "services": 15
    }

# ===== Health Check for Render =====
@app.get("/health")
def health():
    return {"ok": True}

# ===== Example Tools Endpoint =====
@app.get("/tools")
def get_tools():
    return {
        "count": 15,
        "tools": [
            "UnlockTool", "Chimera", "Octoplus", "EFT", "MRT", 
            "And more..."
        ]
    }

# For Galle - Placeholder for future integration
@app.get("/galle/status")
def galle_status():
    return {
        "galle_connected": True,
        "account": "mustafaopen88@gmail.com",
        "api_ready": True,
        "need_api_key": True
    }
