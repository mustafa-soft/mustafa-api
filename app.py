<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MUSTAFA SOFT</title>
<style>
*{margin:0;box-sizing:border-box}
body{background:#0a0a0f;color:#d8e2f0;font:14px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.c{width:100%;max-width:380px;background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.03));border:1px solid rgba(0,229,255,.2);border-radius:26px;padding:26px 20px;box-shadow:0 30px 80px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.12);backdrop-filter:blur(20px)}
.t{font:900 22px/1 system-ui;letter-spacing:.14em;text-align:center;color:#fff}
.t b{color:#00e5ff;text-shadow:0 0 22px rgba(0,229,255,.8)}
.sub{display:flex;gap:8px;justify-content:center;align-items:center;margin:12px 0 18px;color:#7ef0ff;font-size:12.5px;font-weight:700;letter-spacing:.02em}
.dot{width:9px;height:9px;background:#00ff88;border-radius:50%;animation:p 2s infinite;box-shadow:0 0 0 0 rgba(0,255,136,.7)}
@keyframes p{0%{box-shadow:0 0 0 0 rgba(0,255,136,.7)}70%{box-shadow:0 0 0 9px rgba(0,255,136,0)}100%{box-shadow:0 0 0 0 rgba(0,255,136,0)}}
.ep{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:10px 12px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;font-size:12.5px}
.ep i{font-style:normal;color:#a9b6cc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px}
.badge{font-size:10px;font-weight:800;letter-spacing:.08em;padding:4px 8px;border-radius:20px}
.live{background:#00ff88;color:#042a18}
.bak{background:rgba(0,229,255,.15);color:#00e5ff;border:1px solid rgba(0,229,255,.3)}
.st{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0}
.st div{background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.12);border-radius:12px;padding:10px 11px}
.st b{display:block;font-size:10px;letter-spacing:.1em;color:#5fb6c6;margin-bottom:2px}
.st span{font-size:12.5px;color:#eaf8ff;font-weight:600}
.ft{display:flex;justify-content:space-between;margin:16px 0 0;gap:8px}
.ft div{flex:1;text-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:9px 4px;font-size:11px;color:#8aa0ba}
.ft div strong{display:block;color:#00e5ff;font-size:12px;margin-bottom:1px}
.foot{text-align:center;margin-top:18px;font-size:10.5px;letter-spacing:.08em;color:#5a6a82}
a{color:#00e5ff;text-decoration:none}
</style>
</head>
<body>
<div class="c">
<div class="t">MUSTAFA <b>SOFT</b></div>
<div class="sub"><span class="dot"></span> Mustafa GSM API is Running ✅</div>
<div class="ep"><i>mustafa-soft.vercel.app</i><span class="badge live">LIVE</span></div>
<div class="ep"><i>mustafa-api-1.onrender.com</i><span class="badge bak">BACKUP</span></div>
<div class="st">
<div><b>STATUS</b><span>API Running</span></div>
<div><b>GALILEO</b><span>False</span></div>
<div><b>TIME</b><span id="tm">--:--:--</span></div>
<div><b>UPTIME</b><span>99.9%</span></div>
</div>
<div class="ft">
<div><strong>⚡ Fast</strong>Unlock</div>
<div><strong>🔒 Secure</strong>Encrypted</div>
<div><strong>🕒 24/7</strong>Online</div>
</div>
<div class="foot">Made in Al Bauga, Sudan — 2026</div>
</div>
<script>
setInterval(()=>{document.getElementById('tm').textContent=new Date().toLocaleTimeString()},1000)
</script>
</div>
</body>
</html>
