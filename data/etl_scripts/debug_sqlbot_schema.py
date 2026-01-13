import requests
import json
import os

ENDPOINT = os.getenv("SQLBOT_ENDPOINT", "http://sqlbot:8000")

def get_schema():
    try:
        print(f"Fetching schema from {ENDPOINT}/openapi.json")
        res = requests.get(f"{ENDPOINT}/openapi.json", timeout=5)
        if res.status_code == 200:
            data = res.json()
            paths = data.get("paths", {})
            print("Found Endpoints:")
            for path, methods in paths.items():
                if "datasource" in path:
                    for method in methods:
                        print(f"{method.upper()} {path}")
        else:
            print(f"Failed: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_schema()