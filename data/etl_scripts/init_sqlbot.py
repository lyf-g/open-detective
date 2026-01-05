import requests
import time
import os

ENDPOINT = os.getenv("SQLBOT_ENDPOINT", "http://localhost:8000")

def wait_for_sqlbot():
    """Wait for SQLBot service to be ready."""
    print(f"⏳ Waiting for SQLBot at {ENDPOINT}...")
    max_retries = 30
    for i in range(max_retries):
        try:
            # Check the management or health port
            response = requests.get(f"{ENDPOINT}/", timeout=2)
            if response.status_code == 200:
                print("✅ SQLBot is UP!")
                return True
        except Exception:
            pass
        time.sleep(2)
    print("❌ SQLBot failed to start in time.")
    return False

def setup_placeholders():
    """Logic to push initial config to SQLBot via API."""
    # This would typically call SQLBot's API to add a Data Source
    # and configure the default LLM. 
    # For now, we print instructions for the user.
    print("""
🕵️‍♂️ SQLBot DEEP INTEGRATION MANUAL STEP:
1. Access SQLBot Admin at http://localhost:8001
2. Add Data Source: SQLite
3. Path: /opt/sqlbot/db_shared/open_detective.db
4. Configure your LLM API Key in the settings.
    """)

if __name__ == "__main__":
    if wait_for_sqlbot():
        setup_placeholders()
