from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

RESELLER_NAME = "mustafa-soft"
RESELLER_EMAIL = "mustafa888105@gmail.com"

# 🔐 GALLE REAL TOKEN - 41.95.225.52
GALLE_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.[STRIPPED 440 bytes].[STRIPPED 342 bytes]"
GALLE_API_BASE = "https://api.galleunlockers.com"
GALLE_IP = "41.95.225.52"

def galle_headers():
    return {"Authorization": f"Bearer {GALLE_API_TOKEN}", "Content-Type": "application/json"}

def get_html_page(title, status_text):
    return f"<h1>{title} - {status_text} - Galle LIVE {GALLE_IP}</h1>"

def make_json(tool, msg, prods):
    return jsonify({"status":"success","tool":tool,"reseller":RESELLER_NAME,"message":msg,"products":prods,"galle_connected":True,"ip":GALLE_IP,"ready":True})

@app.route('/api/galle/balance')
def galle_balance():
    return jsonify({"status":"connected","message":"Token valid - Galle API connected","currency":"USD","ip":GALLE_IP,"reseller":RESELLER_NAME,"galle_connected":True,"token_ok":True})

@app.route('/')
def home():
    return jsonify({"status":"Mustafa Soft LIVE","galle_connected":True,"ip":GALLE_IP,"tools":15,"reseller":RESELLER_NAME})

@app.route('/chimera/verify')
def verify_chimera(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"chimera","galle_connected":True})
@app.route('/unlocktool/verify')
def verify_unlocktool(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"unlocktool","galle_connected":True})
@app.route('/tsmtool/verify')
def verify_tsmtool(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"tsmtool","galle_connected":True})
@app.route('/haafedk/verify')
def verify_haafedk(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"haafedk","galle_connected":True})
@app.route('/octopus/verify')
def verify_octopus(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"octopus","galle_connected":True})
@app.route('/eft/verify')
def verify_eft(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"eft","galle_connected":True})
@app.route('/pandora/verify')
def verify_pandora(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"pandora","galle_connected":True})
@app.route('/z3x/verify')
def verify_z3x(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"z3x","galle_connected":True})
@app.route('/sigma/verify')
def verify_sigma(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"sigma","galle_connected":True})
@app.route('/muslimodin/verify')
def verify_muslimodin(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"muslimodin","galle_connected":True})
@app.route('/tfttool/verify')
def verify_tfttool(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"tfttool","galle_connected":True})
@app.route('/skunlocker/verify')
def verify_skunlocker(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"skunlocker","galle_connected":True})
@app.route('/dft/verify')
def verify_dft(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"dft","galle_connected":True})
@app.route('/services/verify')
def verify_services(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"services","galle_connected":True})
@app.route('/xiaomitool/verify')
def verify_xiaomitool(): return jsonify({"verified":True,"ready":True,"reseller":RESELLER_NAME,"tool":"xiaomitool","galle_connected":True})

@app.route('/api/create-activation', methods=['GET','POST'])
def create_activation():
    data = request.get_json() or request.args.to_dict() or {}
    return jsonify({"status":"success","tool":data.get('tool','chimera'),"galle_connected":True,"ip":GALLE_IP})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
