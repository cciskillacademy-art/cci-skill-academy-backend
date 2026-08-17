# 🚀 CCI Skill Academy - Backend & Hostinger Deployment Guide

இந்த ஆவணம் உங்கள் **CCI Skill Academy** Backend சிஸ்டத்தை GitHub மற்றும் Hostinger-ல் எப்படி இணைப்பது என்பதை எளிய முறையில் விளக்குகிறது.

---

## 💻 1. உங்கள் கம்ப்யூட்டரில் உடனே இயக்கி பார்ப்பது எப்படி? (Local Testing)

1. `C:\Users\CCISA BALAJI\.gemini\antigravity\scratch\cci-skill-academy-backend` ஃபோல்டருக்கு செல்லுங்கள்.
2. அதில் உள்ள `start_server.bat` ஃபைலை Double Click செய்யுங்கள்.
3. பிரவுசரில் கீழ்வரும் இணைப்புகளைத் திறந்து பாருங்கள்:
   - **Admin Dashboard (அட்மின் பேனல்):** [http://localhost:8000/admin](http://localhost:8000/admin)
     - Username: `admin`
     - Password: `Admin@123`
   - **Certificate Verification (சான்றிதழ் சரிபார்ப்பு):** [http://localhost:8000/verify](http://localhost:8000/verify)
     - Demo Cert ID போட்டு பாருங்கள்: `CCI-2025-0101`
   - **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 2. Hostinger-ல் Backend-ஐ Live செய்வது எப்படி?

Hostinger-ல் 2 வழிகளில் Backend-ஐ இயக்கலாம்:

### வழி A: Hostinger VPS / Cloud Server மூலம் (Recommended for Custom Backend)
1. உங்கள் **Hostinger hPanel**-ல் உள்நுழையவும்.
2. **VPS** அல்லது **Cloud Hosting** செக்ஷனில் Python App அல்லது Node.js App செலக்ட் செய்யவும்.
3. இந்த GitHub கோப்பினை (Repository) Upload செய்து:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. உங்கள் Domain-ல் Reverse Proxy அல்லது Subdomain (எ.கா: `api.cciskillacademy.com`) வழியே இணைக்கலாம்.

---

### வழி B: 100% இலவச Cloud Backend (Render.com / Railway.app) + Hostinger Frontend
*மிக எளிதான & செலவில்லாத வழி!*
1. இந்த கோப்புகளை உங்கள் **GitHub**-ல் Push செய்யவும்.
2. [Render.com](https://render.com) அல்லது [Railway.app](https://railway.app)-ல் இலவசமாக ஒரு Web Service உருவாக்கவும்.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Render உங்களுக்கு ஒரு நேரடி API URL தரும் (எ.கா: `https://cci-api.onrender.com`).
6. உங்கள் Angular Frontend-ல் இந்த API URL-ஐ இணைத்தால் போதும்!

---

## 🔗 3. Frontend-உடன் இணைக்க வேண்டிய API Endpoints (API List)

| வேலை / வசதி | Endpoint | Method | விளக்கம் |
| :--- | :--- | :--- | :--- |
| **Admission Enquiry** | `/api/enquiries` | `POST` | வெப்சைட்டில் Form Submit செய்யும்போது லீட்ஸ் சேமிக்க |
| **Courses List** | `/api/courses` | `GET` | வெப்சைட்டில் கோர்ஸ்கள் காட்ட |
| **Verify Certificate** | `/api/certificates/verify/{cert_no}` | `GET` | ஆன்லைனில் சான்றிதழ் உண்மைதானா என பார்க்க |
| **Admin Login** | `/api/auth/login` | `POST` | அட்மின் உள்நுழைய |
| **Dashboard Stats** | `/api/dashboard/stats` | `GET` | லீட்ஸ் மற்றும் சான்றிதழ் புள்ளிவிவரங்கள் |

---

Career Connext International Skill Academy &copy; 2026
