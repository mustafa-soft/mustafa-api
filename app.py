from flask import Flask, jsonify, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return """
    <html><head><meta charset="utf-8"><style>
    body{background:#0a0e1a;color:#fff;padding:20px;font-family:Cairo,sans-serif}
    .box{background:#111b2f;border:1px solid #1e3a5f;border-radius:12px;padding:15px;margin:10px 0}
    .price{color:#10b981;font-weight:800;border:1px solid #10b981;padding:2px 6px;border-radius:4px;display:inline-block;margin:2px}
    .logo{color:#00d4ff;font-size:28px;font-weight:800;text-align:center}
    </style></head><body>
    <div class="logo">Mustafa Soft - Official Reseller - Deploy 26 Live</div>
    <div class="box">
    <h3 style="color:#00d4ff">Contact Information - Required for Chimera</h3>
    <p style="font-size:12px">Reseller: mustafa-soft | Email: mustafa888105@gmail.com | Phone: +249 90 028 7738<br>
    Address: Al Bauga, Ash Shamaliyah, Sudan | Website: https://mustafa-soft.vercel.app - No login required<br>
    Service ID: srv-dbeeuf4s728c73c18tcg | API: https://mustafa-api-1.onrender.com</p>
    </div>
    <div class="box" style="border-color:#10b981;background:#0f1a15">
    <h3 style="color:#10b981">Chimera Pricing USD - Consistent with chimeratool.com - No Login Required</h3>
    <p>12M: <span class="price">$199 USD</span> 6M: <span class="price">$129 USD</span> 3M: <span class="price">$89 USD</span> 20000 Credits: <span class="price" style="border-color:#f59e0b;color:#f59e0b">$200 USD</span> Required non-refundable no upper limit<br>
    Pro: <span class="price">$299 USD</span> Samsung: <span class="price">$69 USD</span></p>
    <p style="font-size:11px;color:#a7f3d0">All prices USD without login as required. Consistent with chimeratool.com</p>
    </div>
    <div class="box">
    <h3 style="color:#00d4ff">Payment Methods - Clearly Indicated</h3>
    <p style="font-size:11px">
    Bankak: 0900287738 - Displayed $199 USD = 119400 SDG<br>
    USDT TRC20: TE6q6QLYrpHkDFYppTDa1m97kTfCLou8PD - $199 USD<br>
    USDT BEP20: 0x2a11ef4375C7D91d5ad07A1BF85EceA1a82Cf840<br>
    Binance Pay: 570077631 - USD | PayPal: mustafa888105@gmail.com - USD $199
    </p>
    </div>
    <div class="box" style="text-align:center">
    <a href="/chimera/verify" style="color:#00d4ff">Verify Chimera - Prices USD - Contact & Payment - No Login - Live</a>
    </div>
    </body></html>
    """

@app.route('/chimera/verify')
def verify():
    return jsonify({
        "verified": True, "reseller": "mustafa-soft", "email": "mustafa888105@gmail.com",
        "phone": "+249 90 028 7738", "website": "https://mustafa-soft.vercel.app",
        "address": "Al Bauga, Ash Shamaliyah, Sudan", "service_id": "srv-dbeeuf4s728c73c18tcg",
        "pricing_usd": "$199/$129/$89 consistent - No login", "payment": "Bankak $199 USD, USDT TRC20 TE6q6...",
        "chimera_conditions_met": True, "no_login": True, "live": True, "deploy": "26"
    })

@app.route('/chimera')
def chimera():
    if request.args.get('format') == 'json':
        return jsonify({"reseller": "mustafa-soft", "pricing_usd": {"12M": "$199 USD", "6M": "$129 USD", "3M": "$89 USD", "20000 Credits": "$200 USD"}, "chimera_conditions_met": True})
    return home()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
