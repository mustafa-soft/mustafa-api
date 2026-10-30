from flask import Flask, request, jsonify
from flask_cors import CORS
import os, requests, time, hmac, hashlib, base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_env(*keys):
    for k in keys:
        v = os.environ.get(k)
        if v and v.strip(): return v.strip()
    for k in keys:
        v = os.environ.get(k.replace("_","-"))
        if v and v.strip(): return v.strip()
    return ""

GALLE_TOKEN = get_env("GALLE_API_TOKEN","GALLE_API_TOK","ELBROOS_API_TOKEN","ELBROOS_API_T","ELBROOS_API_T...")
GALLE_BASE = get_env("GALLE_API_URL","GALLE-API-URL") or "https://api.galleunlockers.com/api"
GSM_KEY = get_env("GSM_API_KEY","ELBROOS_API_KEY","SHRU_API_KEY","IMEISTAR_API_KEY")
GSM_URL = get_env("GSM_API_URL","ELBROOS_API_URL","SHRU_API_BASE") or "https://api-gsm.elbroos.com/api/shru"
if "galle" in GSM_URL.lower(): GSM_URL = "https://api-gsm.elbroos.com/api/shru"

def b64d(s):
    try:
        if not s: return s
        s=s.strip(); s+='='*(-len(s)%4)
        d=base64.b64decode(s).decode()
        return d if len(d)>5 else s
    except: return s

SHRU_KEY = GSM_KEY or GALLE_TOKEN or b64d(GSM_KEY)
SHRU_BASE = GSM_URL
IP = "41.95.225.52"
SECRET = get_env("SHRU_API_SECRET","ELBROOS_API_SECRET","GSM_API_SECRET")

@app.route('/')
def home():
    return jsonify({"status":"Mustafa GSM API is Running ✅v2705","ip":IP,"galle_len":len(GALLE_TOKEN or ""),"gsm_len":len(GSM_KEY or ""),"base":SHRU_BASE})

@app.route('/api/galle/balance')
def galle_bal():
    t=GALLE_TOKEN or GSM_KEY or SHRU_KEY
    if len(t or "")<10: return jsonify({"galle_connected":False,"len":len(t or ""),"base":GALLE_BASE})
    try:
        r=requests.get(f"{GALLE_BASE.rstrip('/')}/me",headers={"Authorization":f"Bearer {t}"},timeout=10)
        return jsonify({"galle_connected":True,"base":GALLE_BASE,"data":r.json() if "json" in r.headers.get("content-type","") else r.text[:500]})
    except Exception as e: return jsonify({"error":str(e)})

@app.route('/api/shru/balance')
def shru_bal():
    t=GSM_KEY or GALLE_TOKEN or SHRU_KEY
    if len(t or "")<10: return jsonify({"shru_connected":False,"len":len(t or ""),"base":SHRU_BASE})
    try:
        ts=str(int(time.time())); body={"action":"account_info"}; h={"Content-Type":"application/json","X-API-Key":t,"X-Timestamp":ts}
        if SECRET: h["X-Signature"]=hmac.new(SECRET.encode(),f"{ts}account_info".encode(),hashlib.sha256).hexdigest()
        r=requests.post(SHRU_BASE,json=body,headers=h,timeout=15)
        return jsonify({"shru_connected":True,"base":SHRU_BASE,"shru_data":r.json() if "json" in r.headers.get("content-type","") else r.text[:1000]})
    except Exception as e: return jsonify({"error":str(e),"base":SHRU_BASE})

@app.route('/api/create-activation',methods=['GET','POST'])
def create_activation():
    data=request.get_json() or {} if request.is_json else request.args.to_dict()
    if not data:
        try: data=request.get_json(force=True) or {}
        except: data={}
    email=data.get('email','test@test.com'); dur=data.get('duration','12 months'); tool=data.get('tool','chimera')
    return jsonify({"status":"success","message":f"تم استلام طلب تفعيل {tool} - {dur}","email":email,"tool":tool,"note":"عيل يدويا من لوحة الموزع","api_status":"Mustafa GSM API is Running ✅v2705","ip":IP,"base":SHRU_BASE})

if __name__=='__main__': app.run(host='0.0.0.0',port=10000)
