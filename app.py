from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
  return """
    <html><head><meta charset="utf-8"><style>
    body{background:#0a0e1a;color:#fff;padding:20px;font-family:sans-serif}
    .box{background:#111b2f;border:1px solid #1e3a5f;border-radius:12px;padding:15px;margin:10px 0}
    .logo{color:#00d4ff;font-size:28px;font-weight:800;text-align:center}
    </style></head><body>
    <div class="logo">Mustafa Soft - 15 Tools Live API</div>
    <div class="box">
    <h3>System Status</h3>
    <p>All tool APIs are active and ready.</p>
    </div>
    </body></html>
    """


@app.route("/<tool_name>")
def tool_route(tool_name):
  if tool_name not in TOOLS:
    return jsonify({"error": "Tool not found"}), 404
  return jsonify(
      {"reseller": "mustafa-soft", "tool": tool_name.upper(), "status": "Active"}
  )


@app.route("/<tool_name>/verify")
def tool_verify(tool_name):
  if tool_name not in TOOLS:
    return jsonify({"error": "Tool not found"}), 404
  return jsonify({
      "verified": True,
      "reseller": "mustafa-soft",
      "tool": tool_name.upper(),
      "status": "Ready",
  })


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
