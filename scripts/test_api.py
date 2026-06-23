"""
API endpoint test script.
Run: python scripts/test_api.py
"""
import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

# 1. Health check
print("[*] Testing health endpoint...")
req = urllib.request.urlopen(f"{BASE_URL}/")
response = json.loads(req.read())
print(f"[+] Root: {response}")

# 2. Test /search_employee
print("\n[*] Testing /search_employee (Python + Machine Learning bench employees)...")
payload = json.dumps({
    "query": "Find bench employees with Python and Machine Learning skills",
    "top_n": 3
}).encode()
req = urllib.request.Request(
    f"{BASE_URL}/search_employee",
    data=payload,
    headers={"Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(req).read())
print(f"[+] Intent extracted: {result['intent']}")
print(f"[+] Candidates found: {len(result['candidates'])}")
for c in result["candidates"]:
    name = c["name"]
    emp_id = c["emp_id"]
    status = c["status"]
    skills = c["skills"][:3]
    print(f"    - {name} ({emp_id}) | {status} | Skills: {skills}")

# 3. Test /similar_employee
print("\n[*] Testing /similar_employee for E0001...")
payload = json.dumps({"emp_id": "E0001", "limit": 3}).encode()
req = urllib.request.Request(
    f"{BASE_URL}/similar_employee",
    data=payload,
    headers={"Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(req).read())
print(f"[+] Similar employees to E0001:")
for sim in result["similar_employees"]:
    name = sim["name"]
    emp_id = sim["emp_id"]
    shared = sim["shared_skills_count"]
    print(f"    - {name} ({emp_id}) | Shared skills: {shared}")

print("\n" + "="*50)
print("[SUCCESS] FastAPI API is fully operational!")
print("="*50)
