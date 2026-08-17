import urllib.request
import json

def test_api():
    base_url = "http://127.0.0.1:8000"

    print("1. Testing Health Endpoint...")
    with urllib.request.urlopen(f"{base_url}/api/health") as response:
        data = json.loads(response.read().decode())
        print("   Health Result:", data)
        assert data["status"] == "healthy"

    print("\n2. Testing Public Courses Endpoint...")
    with urllib.request.urlopen(f"{base_url}/api/courses") as response:
        courses = json.loads(response.read().decode())
        print(f"   Fetched {len(courses)} courses successfully:")
        for c in courses[:2]:
            print(f"   - {c['title']} ({c['duration']}) - {c['fee']}")

    print("\n3. Testing Certificate Verification...")
    cert_no = "CCI-2025-0101"
    with urllib.request.urlopen(f"{base_url}/api/certificates/verify/{cert_no}") as response:
        cert_data = json.loads(response.read().decode())
        print("   Verification Result:", cert_data["verified"], "Student:", cert_data["data"]["student_name"])
        assert cert_data["verified"] is True

    print("\n4. Testing Admission Enquiry Submission...")
    enquiry_payload = json.dumps({
        "full_name": "Test Student Automated",
        "mobile": "9998887776",
        "email": "student@test.com",
        "course_interest": "Python Programming & Data Analytics",
        "message": "Automated verification test enquiry"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{base_url}/api/enquiries",
        data=enquiry_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        enq_res = json.loads(response.read().decode())
        print("   Enquiry Submit Result:", enq_res)
        assert enq_res["success"] is True

    print("\n5. Testing Admin Login...")
    login_payload = json.dumps({
        "username": "admin",
        "password": "Admin@123"
    }).encode("utf-8")

    login_req = urllib.request.Request(
        f"{base_url}/api/auth/login",
        data=login_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as response:
        login_res = json.loads(response.read().decode())
        print("   Admin Login Result:", login_res["success"], "Token:", login_res["token"])
        assert login_res["success"] is True
        token = login_res["token"]

    print("\n6. Testing Dashboard Stats API...")
    dash_req = urllib.request.Request(
        f"{base_url}/api/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(dash_req) as response:
        dash_res = json.loads(response.read().decode())
        print("   Dashboard Stats:", dash_res["stats"])

    print("\n==========================================")
    print(" ALL BACKEND API TESTS PASSED 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    test_api()
