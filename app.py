from fastapi import FastAPI
import os

app = FastAPI()

def get_token():
    for k in ["GALLE_API_TOK", "GALLE_TOKEN", "GALLE_API_TOKEN", "GALLE_API_TOK...", "GALLE_API_TOK.."]:
        v = os.getenv(k)
        if v and len(v) > 20:
            return v
    return None

@app.get("/")
def home():
    token = get_token()
    has_token = bool(token)
    token_preview = (token[:15] + "..." + token[-10:]) if token and len(token) > 30 else "not found"
    
    return {
        "status": "Running",
        "store": "mustafa-soft.com",
        "galle_token_found": has_token,
        "token_preview": token_preview,
        "galle_connected": False,
        "tools_live": 15,
        "email": "mustafaopen88@gmail.com",
        "message": "Server is Live! Token OK" if has_token else "Add GALLE_API_TOK in Render Environment",
        "endpoints": {
            "docs": "/docs",
            "products_test": "/test-galle",
            "callback": "/callback"
        }
    }

@app.get("/test-galle")
def test_galle():
    import requests
    token = get_token()
    if not token:
        return {"error": "No token found in env"}
    
    base_urls = [
        "https://api.galleunlockers.com",
        "https://galleunlockers.com/api",
        "https://api.galleunlockers.com/api"
    ]
    endpoints = ["/user/me", "/me", "/profile", "/balance", "/user", "/services", "/products"]
    
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    
    for base in base_urls:
        for ep in endpoints:
            url = base + ep
            try:
                r = requests.get(url, headers=headers, timeout=10)
                results.append({"url": url, "status": r.status_code, "ok": r.status_code < 400, "body": r.text[:300]})
                if r.status_code == 200:
                    try:
                        return {"success_url": url, "response": r.json(), "all_tries": results}
                    except:
                        return {"success_url": url, "response": r.text[:500], "all_tries": results}
            except Exception as e:
                results.append({"url": url, "error": str(e)})
    
    return {"message": "Tried all endpoints, check list", "tries": results}

@app.post("/callback")
async def callback(request):
    try:
        from fastapi import Request
        body = await request.json()
    except:
        body = {}
    return {"received": True, "reference_id": body.get("reference_id"), "order_id": body.get("order_id")}
