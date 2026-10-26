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
  cards_html = ""
  for tool in TOOLS:
    cards_html += (
        '<div class="card"><div class="card-title">'
        + tool.upper()
        + '</div><a href="/'
        + tool
        + '" target="_blank" class="btn-api">GET /'
        + tool
        + "</a></div>"
    )

  return (
      "<!DOCTYPE html><html lang='ar' dir='rtl'><head><meta charset='UTF-8'>"
      "<title>Mustafa Soft - API Dashboard</title><style>"
      "body{background:#0b1120;color:#f8fafc;font-family:sans-serif;padding:20px;text-align:center;}"
      "h1{color:#38bdf8;margin-bottom:10px;}"
      ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:15px;margin-top:20px;}"
      ".card{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:15px;text-align:left;}"
      ".card-title{font-size:16px;font-weight:bold;color:#fff;margin-bottom:10px;}"
      ".btn-api{display:block;background:#0284c7;color:#fff;text-decoration:none;padding:8px;border-radius:6px;text-align:center;font-size:12px;font-weight:bold;}"
      ".btn-api:hover{background:#0369a1;}"
      "</style></head><body>"
      "<h1>Mustafa Soft - API Dashboard</h1>"
      "<p>15 Maintenance Tools Control Center</p>"
      '<div class="grid">'
      + cards_html
      + "</div></body></html>"
  )


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
