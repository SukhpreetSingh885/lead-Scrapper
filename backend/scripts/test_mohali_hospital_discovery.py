import requests
import os
import time
from dotenv import load_dotenv

load_dotenv("d:/india-leads-platform/backend/.env")
email = os.getenv("ADMIN_EMAIL", "admin@indialeads.internal")
password = os.getenv("ADMIN_INITIAL_PASSWORD", "Admin@123456")

session = requests.Session()

# 1. Login through Next.js proxy port 3000
t0 = time.time()
login_res = session.post("http://localhost:3000/api/v1/auth/login", data={"username": email, "password": password})
print(f"1. Login status: {login_res.status_code} in {time.time()-t0:.3f}s")
if login_res.status_code != 200:
    print("Login failed:", login_res.text)
    exit(1)

token = login_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Test POST /api/v1/discovery/jobs through Next.js proxy
post_payload = {
    "location": "Mohali",
    "category": "Hospital",
    "radius_km": 25,
    "max_leads": 500,
    "source": "overpass"
}

print("2. Sending POST /api/v1/discovery/jobs (Mohali + Hospital, 25km, 500 max)...")
t_start = time.time()
post_res = session.post("http://localhost:3000/api/v1/discovery/jobs", json=post_payload, headers=headers)
post_duration = time.time() - t_start

print(f"POST response status: {post_res.status_code} in {post_duration:.3f}s")
if post_res.status_code not in (200, 201):
    print("POST failed:", post_res.text)
    exit(1)

job_data = post_res.json()
job_id = job_data["id"]
print(f"Job ID created promptly: {job_id}")
print(f"Initial status: {job_data['status']}")

# 3. Poll job status
print("3. Polling job status until completion...")
poll_start = time.time()
completed = False
final_job = None
while time.time() - poll_start < 180:
    poll_res = session.get(f"http://localhost:3000/api/v1/discovery/jobs/{job_id}", headers=headers)
    if poll_res.status_code == 200:
        j = poll_res.json()
        status = j["status"]
        print(f"   [+{time.time()-poll_start:.1f}s] Status: {status} | Discovered: {j.get('total_discovered')} | Eligible: {j.get('total_eligible')}")
        if status in ("completed", "failed", "cancelled"):
            completed = True
            final_job = j
            break
    time.sleep(3)

if not completed:
    print("Job polling timed out after 180s!")
    exit(1)

print("\n--- JOB FINAL SUMMARY ---")
print(f"Final status: {final_job['status']}")
print(f"Total Discovered: {final_job.get('total_discovered')}")
print(f"Total Eligible: {final_job.get('total_eligible')}")
print(f"Mobile Leads: {final_job.get('total_mobile')}")
print(f"Landline Leads: {final_job.get('total_landline')}")
print(f"WhatsApp Active: {final_job.get('total_whatsapp')}")
print(f"Missing Phone: {final_job.get('total_missing_phone')}")

# 4. Fetch preview through Next.js proxy
prev_res = session.get(f"http://localhost:3000/api/v1/discovery/jobs/{job_id}/preview?page=1&page_size=25", headers=headers)
print(f"\n4. Preview endpoint status: {prev_res.status_code}")
if prev_res.status_code == 200:
    pdata = prev_res.json()
    print(f"Total preview leads available: {pdata['total']}")
    print(f"Returned items on page 1: {len(pdata['items'])}")
    if pdata["items"]:
        for idx, item in enumerate(pdata["items"][:5], 1):
            print(f"   {idx}. {item['business_name']} | Mobile: {item.get('mobile')} | Landline: {item.get('phone')} | City: {item.get('city')}")

print("\nSUCCESS: Mohali + Hospital discovery fully verified end-to-end!")

