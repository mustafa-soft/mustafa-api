from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import datetime
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}, r"/": {"origins": "*"}})

# الإعدادات - من Render Environment
GALLE_API_URL = os.getenv("GALLE_API_URL", "https://api.galleunlockers.com").rstrip("/")
GALLE_API_TOKEN = os.getenv("GALLE_API_TOKEN", "")
GSM_API_URL = "https://api2-gsm.elbroos.com/"
GSM_API_KEY = os.getenv("GSM_API_KEY", "")

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mustafa Soft - API Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;900&display=swap" rel="stylesheet">
<style>
*{font-family:'Tajawal',sans-serif;box-sizing:border-box}
body{background:#070b18;color:#fff;margin:0;padding:16px}
.container{max-width:1100px;margin:auto}
.head{background:linear-gradient(135deg,#00ffa6,#00c2ff);color:#000;padding:20px;border-radius:20px;display:flex;justify-content:space-between;flex-wrap:wrap}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-top:16px}
.card{background:#121a33;border:1px solid #1e2e5a;border-radius:18px;padding:18px}
.card h3{color:#00ffa6;margin:0 0 10px}
.badge{padding:5px 12px;border-radius:99px;font-size:12px;font-weight:800}
.green{background:#00ffa61a;color:#00ffa6;border:1px solid #00ffa640}
pre{background:#070b18;border:1px solid #1e2e5a;border-radius:12px;padding
