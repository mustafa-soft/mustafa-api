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
  return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mustafa Soft - API Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
        body { background-color: #0b1120; color: #f8fafc; padding: 20px 15px; direction: rtl; }
        .container { max-width: 1100px; margin: 0 auto; }
        
        /* Header */
        header { text-align: center; padding: 20px 0 30px; }
        .main-title { font-size: 38px; font-weight: 800; color: #38bdf8; text-shadow: 0 0 15px rgba(56,189,248,0.4); margin-bottom: 8px; }
        .sub-title { font-size: 13px; color: #94a3b8; margin-bottom: 6px; }
        .badge-info { font-size: 12px; color: #64748b; margin-bottom: 15px; }
        .status-pill { display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-bottom: 20px; }
        .dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
        
        .action-btns { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
        .btn-site { background: #3b82f6; color: #fff; text-decoration: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 14px rgba(59,130,246,0.4); transition: 0.3s; }
        .btn-site:hover { background: #2563eb; }
        .btn-wa { background: #0f172a; color: #94a3b8; border: 1px solid #334155; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 500; }
        
        /* Grid */
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; margin-top: 25px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; position: relative; }
        .card-title { font-size: 18px; font-weight: bold; color: #ffffff; margin-bottom: 8px; display: flex; align-items: center; justify-content: center; gap: 6px; }
        .card-desc { font-size: 12px; color: #94a3b8; margin-bottom: 16px; line-height: 1.5; min-height: 36px; }
        .btn-api { display: block; width: 100%; padding: 10px; border-radius: 8px; color: #fff; text-decoration: none; font-size: 13px; font-weight: bold; text-align: center; transition: 0.2s; }
        
        /* Button Colors */
        .bg-blue { background: #0284c7; } .bg-blue:hover { background: #0369a1; }
        .bg-cyan { background: #06b6d4; } .bg-cyan:hover { background: #0891b2; }
        .bg-teal { background: #0d9488; } .bg-teal:hover { background: #0f766e; }
        .bg-orange { background: #ea580c; } .bg-orange:hover { background: #c2410c; }
        .bg-red { background: #dc2626; } .bg-red:hover { background: #b91c1c; }
        .bg-purple { background: #9333ea; } .bg-purple:hover { background: #7e22ce; }
        .bg-green { background: #16a34a; } .bg-green:hover { background: #15803d; }
        .bg-pink { background: #db2777; } .bg-pink:hover { background: #be185d; }
        
        /* Table Section */
        .routes-section { margin-top: 40px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
        .routes-title { font-size: 16px; font-weight: bold; color: #38bdf8; margin-bottom: 15px; text-align: right; }
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th, td { padding: 12px 15px; border-bottom: 1px solid #334155; }
        th { color: #64748b; font-weight: 600; text-align: right; }
        td { color: #cbd5e1; direction: ltr; text-align: left; }
        td a { color: #38bdf8; text-decoration: none; }
        td a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1 class="main-title">Mustafa Soft</h1>
            <p class="sub-title">Chimera & UnlockTool & TSM & Haafedh & Octopus & EFT & Pandora & Z3X & Sigma & Muslim Odin & TFT & SK Unlocker & DFT & Services & Xiaomi Tool</p>
            <p class="badge-info">Reseller API | Tools Live - mustafa-soft 15</p>
            <div class="status-pill"><span class="dot"></span> DFT Multi Ready</div>
            <div class="action-btns">
                <a href="https://mustafa-soft.vercel.app/" target="_blank" class="btn-site">الموقع الرسمي</a>
                <a href="https://wa.me/249900287738" target="_blank" class="btn-wa">واتساب: 0900287738 💬</a>
            </div>
        </header>

        <div class="grid">
            <!-- 1 -->
            <div class="card">
                <div class="card-title">Chimera Tool ⚙️</div>
                <div class="card-desc">تفعيل رسمي - 12 / 6 / 3 شهر<br>هواتف ومجاناً</div>
                <a href="/chimera" target="_blank" class="btn-api bg-cyan">عرض Chimera API</a>
            </div>
            <!-- 2 -->
            <div class="card">
                <div class="card-title">UnlockTool 🔓</div>
                <div class="card-desc">تفعيل رسمي - 12 / 6 / 3 شهر<br>فكت شفرة و FRP</div>
                <a href="/unlocktool" target="_blank" class="btn-api bg-blue">عرض UnlockTool API</a>
            </div>
            <!-- 3 -->
            <div class="card">
                <div class="card-title">TSM Tool ⚙️</div>
                <div class="card-desc">تفعيل رسمي - TSM Pro<br>سامسونج و MTK</div>
                <a href="/tsm" target="_blank" class="btn-api bg-cyan">عرض TSM API</a>
            </div>
            <!-- 4 -->
            <div class="card">
                <div
