import requests
import time
import os
import json
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

ENDPOINT = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")
USERNAME = os.getenv("SQLBOT_USERNAME", "admin")
PASSWORD = os.getenv("SQLBOT_PASSWORD", "SQLBot@123456")

# MySQL Details from Env
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD") or os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "open_detective")

# LLM Details
LLM_PROVIDER = os.getenv("SQLBOT_LLM_PROVIDER", "openai")
LLM_KEY = os.getenv("SQLBOT_LLM_API_KEY", "")
LLM_BASE = os.getenv("SQLBOT_LLM_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("SQLBOT_LLM_MODEL", "gpt-3.5-turbo")

def get_public_key():
    try:
        res = requests.get(f"{ENDPOINT}/api/v1/system/config/key", timeout=5)
        if res.status_code == 200:
            data = res.json().get("data", {})
            return data.get("public_key") or data.get("publicKey")
    except Exception as e:
        print(f"Error getting PK: {e}")
    return None

def encrypt(text, pk):
    key = RSA.importKey(pk)
    cipher = PKCS1_v1_5.new(key)
    return base64.b64encode(cipher.encrypt(text.encode())).decode('utf-8')

def login():
    pk = get_public_key()
    if not pk: return None
    payload = {
        "username": encrypt(USERNAME, pk),
        "password": encrypt(PASSWORD, pk),
        "grant_type": "password"
    }
    try:
        res = requests.post(f"{ENDPOINT}/api/v1/login/access-token", data=payload)
        if res.status_code == 200:
            return res.json().get("data", {}).get("access_token") or res.json().get("access_token")
    except Exception as e:
        print(f"Login failed: {e}")
    return None

def configure_datasource(token):
    if token and not token.startswith("Bearer "): token = f"Bearer {token}"
    headers = {"X-SQLBOT-TOKEN": token, "Content-Type": "application/json"}
    
    # Payload structure for DataEase/SQLBot usually involves 'connection' details
    config_dict = {
        "host": DB_HOST,
        "port": DB_PORT,
        "username": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
        "extraParams": "characterEncoding=utf8&useSSL=false"
    }
    
    payload = {
        "name": "OpenDetectiveDB",
        "type": "mysql",
        "configuration": json.dumps(config_dict),
        "status": "ENABLE"
    }
    
    print(f"🔌 Configuring Datasource: {DB_HOST}...")
    try:
        # Check existing
        list_res = requests.get(f"{ENDPOINT}/api/v1/datasource", headers=headers)
        if list_res.status_code == 200:
            print(f"   Existing Datasources: {len(list_res.json().get('data', []))}")
        
        # Try POST /api/v1/datasource (standard) or /api/v1/datasource/create
        endpoints = [
            f"{ENDPOINT}/api/v1/datasource",
            f"{ENDPOINT}/api/v1/datasource/create",
            f"{ENDPOINT}/api/v1/datasource/add"
        ]
        
        for ep in endpoints:
            res = requests.post(ep, json=payload, headers=headers)
            if res.status_code == 200:
                print(f"✅ Datasource configured via {ep}.")
                return
            elif res.status_code != 404 and res.status_code != 405:
                 print(f"   {ep} returned {res.status_code} {res.text}")

        print(f"⚠️ Datasource config failed on all attempts.")
    except Exception as e:
        print(f"❌ Datasource config failed: {e}")

def configure_llm(token):
    if not LLM_KEY or len(LLM_KEY) < 5:
        print("⏭️  Skipping LLM Config (Key missing)")
        return

    if token and not token.startswith("Bearer "): token = f"Bearer {token}"
    headers = {"X-SQLBOT-TOKEN": token, "Content-Type": "application/json"}
    
    # Generic structure guess
    payload = {
        "provider": LLM_PROVIDER,
        "config": {
            "apiKey": LLM_KEY,
            "apiBase": LLM_BASE,
            "model": LLM_MODEL
        },
        "status": "ENABLE"
    }
    
    print(f"🧠 Configuring LLM ({LLM_PROVIDER})...")
    try:
        # Try multiple potential endpoints
        endpoints = [
            f"{ENDPOINT}/api/v1/llm/save",
            f"{ENDPOINT}/api/v1/system/parameter/llm",
            f"{ENDPOINT}/api/v1/llm/create"
        ]
        
        success = False
        for ep in endpoints:
            res = requests.post(ep, json=payload, headers=headers)
            if res.status_code == 200:
                print(f"✅ LLM configured via {ep}.")
                success = True
                break
        
        if not success:
            print(f"⚠️ LLM config failed on all attempts.")
    except Exception as e:
        print(f"❌ LLM config failed: {e}")

def main():
    # Allow manually disabling via env
    if os.getenv("SQLBOT_AUTO_CONFIG", "false").lower() != "true":
        print("Skipping auto-config.")
        return

    print("⏳ Waiting for SQLBot to be ready...")
    for _ in range(30):
        try:
            if requests.get(f"{ENDPOINT}/").status_code == 200: break
        except: pass
        time.sleep(2)
        
    token = login()
    if token:
        print("🔑 Logged in to SQLBot.")
        configure_datasource(token)
        configure_llm(token)
    else:
        print("❌ Could not login to SQLBot.")

if __name__ == "__main__":
    main()