from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# قائمة الأدوات الـ 15 لتوليد مساراتها تلقائياً وتجنب خطأ Not Found
TOOLS = [
    "chimera",
    "tsm",
    "unlocktool",
    "eft",
    "octopus",
    "haafedh",
    "sigma",
    "z3x",
    "pandora",
    "sk",
    "tft",
    "muslim_odin",
    "xiaomi",
    "services",
    "dft_multi",
]


@app.route("/")
def home():
  tools_links = "".join([
      f"<div style='margin:5px 0;'><a href='/{tool}'"
      f" style='color:#00d4ff'>- {tool.upper()} API</a> | <a"
      f" href='/{tool}/verify' style='color:#10b981'>Verify</a></div>"
      for tool in TOOLS
  ])

  return f"""
    <html><head><meta charset="utf-8"><style>
    body{{background:#0a0e1a;color:#fff;padding:20px;font-family:Cairo,sans-serif}}
    .box{{background:#111b2f;border:1px solid #1e3a5f;border-radius:12px;padding:15px;margin:10px 0}}
    .price{{color:#10b981;font-weight:800;border:1px solid #10b981;padding:2px 6px;border-radius:4px;display:inline-block;margin:2px}}
    .logo{{color:#00d4ff;font-size:28px;font-weight:800;text-align:center}}
    a{{text-decoration:none}}
    </style></head><body>
    <div class="logo">Mustafa Soft - Official Reseller API - 15 Tools Live</div>
    
    <div class="box">
    <h3 style="color:#00d4ff">Contact Information</h3>
    <p style="font-size:12px">Reseller: mustafa-soft | Email: mustafa888105@gmail.com | Phone: +249 90 028 7738<br>
    Address: Al Bauga, Ash Shamaliyah, Sudan | Service ID: srv-dbeeuf4s728c73c18tcg</p>
    </div>

    <div class="box" style="border-color:#10b981;background:#0f1a15">
    <h3 style="color:#10b981">Chimera Pricing USD</h3>
    <p>12M: <span class="price">$199 USD</span> 6M: <span class="price">$129 USD</span> 3M: <span class="price">$89 USD</span> Pro: <span class="price">$299 USD</span></p>
    </div>

    <div class="box">
    <h3 style="color:#00d4ff">Available API Routes for all 15 Tools:</h3>
    {tools_links}
    </div>
    </body></html>
    """


# مسارات خاصة لأداة Chimera
@app.route("/chimera/verify")
def verify_chimera():
  return jsonify({
      "verified": True,
      "reseller": "mustafa-soft",
      "tool": "Chimera",
      "email": "mustafa888105@gmail.com",
      "phone": "+249 90 028 7738",
      "pricing_usd": "$199/$129/$89 consistent - No login",
      "live": True,
  })


@app.route("/chimera")
def chimera():
  return jsonify({
      "reseller": "mustafa-soft",
      "tool": "Chimera",
      "pricing_usd": {
          "12M": "$199 USD",
          "6M": "$129 USD",
          "3M": "$89 USD",
          "20000 Credits": "$200 USD",
      },
      "chimera_conditions_met": True,
  })


# توليد مسارات بقية الأدوات تلقائياً لضمان عدم ظهور Not Found
def register_tool(tool_name):
  @app.route(f"/{tool_name}")
  def tool_route():
    return jsonify({
        "reseller": "mustafa-soft",
        "tool": tool_name.upper(),
        "status": "Active & Ready",
        "phone": "+249 90 028 7738",
    })

  @app.route(f"/{tool_name}/verify")
  def tool_verify_route():
    return jsonify({
        "verified": True,
        "reseller": "mustafa-soft",
        "tool": tool_name.upper(),
        "status": "Ready",
        "contact": "mustafa888105@gmail.com",
    })


for t in TOOLS:
  if t != "chimera":
    register_tool(t)

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
