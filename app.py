
from fastapi import FastAPI, Request
import os, requests

app = FastAPI()

# التوكن من Render
TOKEN = os.getenv("GALLE_API_TOK") or os.getenv("GALLE_API_TOKEN") or os.getenv("GALLE_TOKEN")
BASE = "https://api.galleunlockers.com"

def get_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "Mozilla/5.0 MustafaSoft",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@app.get("/")
def home():
    return {
        "status": "Running",
        "store": "mustafa-soft.com",
        "galle_token_found": bool(TOKEN),
        "base": BASE,
        "endpoints": ["/account", "/products", "/order", "/callback"],
        "note": "Use /account to test connection"
    }

@app.get("/account")
def account():
    try:
        r = requests.get(f"{BASE}/account", headers=get_headers(), timeout=20)
        return {"http": r.status_code, "data": r.json() if r.headers.get("content-type","").startswith("application/json") else r.text[:500]}
    except Exception as e:
        return {"error": str(e), "token_found": bool(TOKEN)}

@app.get("/products")
def products():
    try:
        r = requests.get(f"{BASE}/products", headers=get_headers(), timeout=20)
        try:
            data = r.json()
            return data
        except:
            return {"http": r.status_code, "text": r.text[:2000]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/products/{product_id}")
def product_detail(product_id: str):
    try:
        r = requests.get(f"{BASE}/products?product_id={product_id}", headers=get_headers(), timeout=20)
        return r.json() if "application/json" in r.headers.get("content-type","") else {"http": r.status_code, "text": r.text[:2000]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/callback")
async def callback(request: Request):
    body = await request.json()
    # هنا بتستقبل اشعارات Galle لما الطلب يخلص
    print("CALLBACK:", body)
    return {"status": "received"}

@app.get("/test-galle")
def test_galle():
    results = {}
    for path in ["/account", "/products"]:
        try:
            r = requests.get(f"{BASE}{path}", headers=get_headers(), timeout=15)
            try:
                j = r.json()
                results[path] = {"status": r.status_code, "ok": r.status_code==200, "sample": str(j)[:1000]}
            except:
                results[path] = {"status": r.status_code, "text": r.text[:800]}
        except Exception as e:
            results[path] = {"error": str(e)}
    return results
