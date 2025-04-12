import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
import json

# Now import your FastAPI app using an absolute import.
from app.app import app

client = TestClient(app)

def main():
    payload = {
        "url": "https://www.google.com/maps/place/Safeway/@33.3996131,-112.0180752,12z/data=!4m10!1m2!2m1!1sSafeway!3m6!1s0x872b08eb1f672da9:0xada6b30643433178!8m2!3d33.4090163!4d-111.9251615!15sCgdTYWZld2F5IgOIAQFaCSIHc2FmZXdheZIBDWdyb2Nlcnlfc3RvcmXgAQA!16s%2Fg%2F1tm88x9m?entry=ttu&g_ep=EgoyMDI1MDQwOS4wIKXMDSoJLDEwMjExNjM5SAFQAw%3D%3D"
    }
    print("Sending POST /analyze with payload:")
    print(json.dumps(payload, indent=2))
    response = client.post("/analyze", json=payload)
    print("\nStatus Code:", response.status_code)
    try:
        response_data = response.json()
        print("Response JSON:")
        print(json.dumps(response_data, indent=2))
    except Exception as e:
        print("Response text:", response.text)

if __name__ == "__main__":
    main()
