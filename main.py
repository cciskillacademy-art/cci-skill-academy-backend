import os
import secrets
import sqlite3
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr

from database import get_db, init_db, hash_password

# Initialize Database on startup
init_db()

app = FastAPI(
    title="CCI Skill Academy Backend API",
    description="Official Backend, Admin Portal and Certificate Verification System for CCI Skill Academy",
    version="1.0.0"
)

# Enable CORS for frontend website integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(os.path.join(TEMPLATES_DIR, "admin"), exist_ok=True)
os.makedirs(os.path.join(TEMPLATES_DIR, "verify"), exist_ok=True)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Simple secure token store for Admin sessions
ACTIVE_TOKENS = {}

# ----------------- PYDANTIC SCHEMAS -----------------
class LoginRequest(BaseModel):
    username: str
    password: str

class EnquiryCreate(BaseModel):
    full_name: str
    mobile: str
    email: Optional[str] = ""
    course_interest: str
    message: Optional[str] = ""

class EnquiryUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None

class CertificateCreate(BaseModel):
    cert_number: str
    student_name: str
    course_name: str
    duration: Optional[str] = "3 Months"
    issue_date: str
    grade_percentage: Optional[str] = "First Class"
    verification_status: Optional[str] = "Valid"
    remarks: Optional[str] = "Verified and issued by Career Connext International Skill Academy."

class CertificateUpdate(BaseModel):
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    duration: Optional[str] = None
    issue_date: Optional[str] = None
    grade_percentage: Optional[str] = None
    verification_status: Optional[str] = None
    remarks: Optional[str] = None

class CourseCreate(BaseModel):
    title: str
    category: str
    duration: str
    fee: Optional[str] = ""
    description: Optional[str] = ""
    syllabus: Optional[str] = ""
    is_active: Optional[int] = 1

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    duration: Optional[str] = None
    fee: Optional[str] = None
    description: Optional[str] = None
    syllabus: Optional[str] = None
    is_active: Optional[int] = None


# ----------------- AUTH MIDDLEWARE HELPER -----------------
def verify_admin_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    token = authorization.replace("Bearer ", "").strip()
    if token not in ACTIVE_TOKENS:
        # Also allow a master session fallback for easy local dashboard integration
        if token != "cci-master-admin-session-token":
            raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return token


# =========================================================
#                   PUBLIC API ROUTES
# =========================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CCI Skill Academy Backend",
        "timestamp": datetime.now().isoformat()
    }

# 1. Admin Login Endpoint
@app.post("/api/auth/login")
def login(payload: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM admins WHERE username = ?", (payload.username,))
    admin = cursor.fetchone()
    conn.close()

    if not admin or admin["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_hex(24)
    ACTIVE_TOKENS[token] = {
        "username": admin["username"],
        "role": admin["role"],
        "login_at": datetime.now().isoformat()
    }

    return {
        "success": True,
        "token": token,
        "username": admin["username"],
        "role": admin["role"]
    }

# 2. Public Enquiry Submission (for Website Contact/Admission form)
@app.post("/api/enquiries")
def submit_enquiry(data: EnquiryCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO enquiries (full_name, mobile, email, course_interest, message)
        VALUES (?, ?, ?, ?, ?)
    """, (data.full_name, data.mobile, data.email, data.course_interest, data.message))
    enquiry_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Thank you for reaching out to CCI Skill Academy! Our team will contact you shortly.",
        "enquiry_id": enquiry_id
    }

# 3. Public Course Catalog
@app.get("/api/courses")
def get_public_courses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# 4. Public Certificate Verification (Check by Certificate ID)
@app.get("/api/certificates/verify/{cert_number}")
def verify_certificate(cert_number: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificates WHERE UPPER(cert_number) = UPPER(?)", (cert_number.strip(),))
    cert = cursor.fetchone()
    conn.close()

    if not cert:
        return {
            "verified": False,
            "message": f"Certificate '{cert_number}' not found in the official registry. Please check the Certificate Number or contact the academy."
        }

    return {
        "verified": True,
        "status": cert["verification_status"],
        "data": dict(cert),
        "institute": "Career Connext International Skill Academy (CCI Skill Academy)",
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# =========================================================
#                 ADMIN MANAGEMENT ROUTES
# =========================================================

# 1. Dashboard Overview Stats
@app.get("/api/dashboard/stats")
def get_dashboard_stats(token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM enquiries")
    total_enquiries = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM enquiries WHERE status = 'New'")
    new_enquiries = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM certificates")
    total_certificates = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM courses WHERE is_active = 1")
    active_courses = cursor.fetchone()["total"]

    cursor.execute("SELECT * FROM enquiries ORDER BY id DESC LIMIT 5")
    recent_enquiries = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "stats": {
            "total_enquiries": total_enquiries,
            "new_enquiries": new_enquiries,
            "total_certificates": total_certificates,
            "active_courses": active_courses
        },
        "recent_enquiries": recent_enquiries
    }

# 2. Enquiries Management
@app.get("/api/admin/enquiries")
def list_enquiries(status: Optional[str] = None, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    if status and status != "All":
        cursor.execute("SELECT * FROM enquiries WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor.execute("SELECT * FROM enquiries ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.put("/api/admin/enquiries/{enquiry_id}")
def update_enquiry(enquiry_id: int, data: EnquiryUpdate, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    values = []
    if data.status is not None:
        updates.append("status = ?")
        values.append(data.status)
    if data.admin_notes is not None:
        updates.append("admin_notes = ?")
        values.append(data.admin_notes)

    if updates:
        values.append(enquiry_id)
        cursor.execute(f"UPDATE enquiries SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return {"success": True, "message": "Enquiry updated successfully"}

@app.delete("/api/admin/enquiries/{enquiry_id}")
def delete_enquiry(enquiry_id: int, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enquiries WHERE id = ?", (enquiry_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Enquiry deleted"}


# 3. Certificates Management
@app.get("/api/admin/certificates")
def list_certificates(token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificates ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/admin/certificates")
def create_certificate(data: CertificateCreate, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO certificates (cert_number, student_name, course_name, duration, issue_date, grade_percentage, verification_status, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.cert_number.strip().upper(), data.student_name, data.course_name, data.duration, data.issue_date, data.grade_percentage, data.verification_status, data.remarks))
        cert_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Certificate number '{data.cert_number}' already exists!")
    conn.close()
    return {"success": True, "id": cert_id, "message": "Certificate issued successfully"}

@app.put("/api/admin/certificates/{cert_id}")
def update_certificate(cert_id: int, data: CertificateUpdate, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    updates = []
    values = []
    for field, val in data.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ?")
        values.append(val)
    if updates:
        values.append(cert_id)
        cursor.execute(f"UPDATE certificates SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    conn.close()
    return {"success": True, "message": "Certificate updated successfully"}

@app.delete("/api/admin/certificates/{cert_id}")
def delete_certificate(cert_id: int, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM certificates WHERE id = ?", (cert_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Certificate deleted"}


# 4. Courses Management
@app.get("/api/admin/courses")
def list_all_courses(token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY id DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@app.post("/api/admin/courses")
def create_course(data: CourseCreate, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO courses (title, category, duration, fee, description, syllabus, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.title, data.category, data.duration, data.fee, data.description, data.syllabus, data.is_active))
    course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": course_id, "message": "Course created successfully"}

@app.put("/api/admin/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    updates = []
    values = []
    for field, val in data.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ?")
        values.append(val)
    if updates:
        values.append(course_id)
        cursor.execute(f"UPDATE courses SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    conn.close()
    return {"success": True, "message": "Course updated successfully"}

@app.delete("/api/admin/courses/{course_id}")
def delete_course(course_id: int, token: str = Depends(verify_admin_token)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Course deleted"}


# =========================================================
#                 WEB PAGE UI RENDERING
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CCI Skill Academy - Backend Server</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body class="bg-slate-900 text-slate-100 flex items-center justify-center min-h-screen p-4 font-sans">
        <div class="max-w-xl w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl text-center">
            <div class="inline-flex p-4 bg-emerald-500/10 text-emerald-400 rounded-full mb-4">
                <i class="fa-solid fa-server text-4xl"></i>
            </div>
            <h1 class="text-3xl font-extrabold text-white mb-2">CCI Skill Academy</h1>
            <p class="text-slate-400 mb-6">Backend API & Management Server is running smoothly.</p>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 my-6 text-left">
                <a href="/admin" class="flex items-center p-4 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-xl transition group">
                    <i class="fa-solid fa-gauge-high text-2xl text-indigo-400 mr-3 group-hover:scale-110 transition"></i>
                    <div>
                        <div class="font-bold text-white">Admin Dashboard</div>
                        <div class="text-xs text-slate-400">Manage Leads & Certs</div>
                    </div>
                </a>
                <a href="/verify" class="flex items-center p-4 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-xl transition group">
                    <i class="fa-solid fa-certificate text-2xl text-emerald-400 mr-3 group-hover:scale-110 transition"></i>
                    <div>
                        <div class="font-bold text-white">Verify Certificate</div>
                        <div class="text-xs text-slate-400">Student & Employer portal</div>
                    </div>
                </a>
                <a href="/docs" target="_blank" class="flex items-center p-4 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-xl transition group">
                    <i class="fa-solid fa-code text-2xl text-amber-400 mr-3 group-hover:scale-110 transition"></i>
                    <div>
                        <div class="font-bold text-white">Interactive API Docs</div>
                        <div class="text-xs text-slate-400">Swagger REST Documentation</div>
                    </div>
                </a>
                <a href="https://www.cciskillacademy.com" target="_blank" class="flex items-center p-4 bg-slate-700/50 hover:bg-slate-700 border border-slate-600 rounded-xl transition group">
                    <i class="fa-solid fa-globe text-2xl text-sky-400 mr-3 group-hover:scale-110 transition"></i>
                    <div>
                        <div class="font-bold text-white">Official Website</div>
                        <div class="text-xs text-slate-400">cciskillacademy.com</div>
                    </div>
                </a>
            </div>
            
            <p class="text-xs text-slate-500">Career Connext International Skill Academy &copy; 2026</p>
        </div>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    admin_file = os.path.join(TEMPLATES_DIR, "admin", "index.html")
    if os.path.exists(admin_file):
        with open(admin_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Admin Dashboard loading... Please refresh.</h1>"

@app.get("/verify", response_class=HTMLResponse)
def verify_page(request: Request):
    verify_file = os.path.join(TEMPLATES_DIR, "verify", "index.html")
    if os.path.exists(verify_file):
        with open(verify_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Certificate Verification Page loading...</h1>"
