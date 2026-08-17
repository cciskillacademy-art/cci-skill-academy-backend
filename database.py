import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "cci_academy.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Admin Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Enquiries (Leads / Student Admissions) Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT,
        course_interest TEXT NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'New',
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Certificates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cert_number TEXT UNIQUE NOT NULL,
        student_name TEXT NOT NULL,
        course_name TEXT NOT NULL,
        duration TEXT,
        issue_date TEXT NOT NULL,
        grade_percentage TEXT,
        verification_status TEXT DEFAULT 'Valid',
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 4. Courses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        duration TEXT NOT NULL,
        fee TEXT,
        description TEXT,
        syllabus TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Default Admin Seed (if not exists)
    cursor.execute("SELECT id FROM admins WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", hash_password("Admin@123"), "admin")
        )

    # Initial Demo Courses Seed (if empty)
    cursor.execute("SELECT COUNT(*) as cnt FROM courses")
    if cursor.fetchone()["cnt"] == 0:
        sample_courses = [
            ("Full Stack Web Development (MERN / Python)", "Software & IT", "3 Months", "Rs. 15,000", "Master HTML, CSS, JavaScript, React, Node.js / Python and building live web applications.", "Frontend, Backend, Database, Cloud Deployment, Live Projects"),
            ("Python Programming & Data Analytics", "Programming", "2 Months", "Rs. 10,000", "Hands-on Python, Pandas, NumPy, SQL, and Data Visualization with PowerBI/Matplotlib.", "Core Python, OOPs, Data Processing, SQL Database, Real-world Projects"),
            ("Spoken English & Communication Mastery", "Language & Soft Skills", "45 Days", "Rs. 4,500", "Fluent English speaking, accent neutralization, interview preparation and public speaking.", "Grammar Essentials, Daily Conversations, Mock Interviews, Group Discussions"),
            ("DCA & Tally Prime with GST", "Finance & Office Skills", "2 Months", "Rs. 6,000", "Comprehensive computer application course with MS Office and Tally Prime accounting.", "MS Word, Excel, PowerPoint, Tally Prime, GST Invoicing, E-Way Bill"),
            ("Graphic Design & Video Editing", "Design & Multimedia", "2 Months", "Rs. 8,000", "Adobe Photoshop, Illustrator, Premiere Pro, and Canva for creative career.", "Logo Design, Social Media Posters, Video Editing, Motion Graphics")
        ]
        for course in sample_courses:
            cursor.execute(
                "INSERT INTO courses (title, category, duration, fee, description, syllabus) VALUES (?, ?, ?, ?, ?, ?)",
                course
            )

    # Initial Demo Certificate Seed (if empty)
    cursor.execute("SELECT COUNT(*) as cnt FROM certificates")
    if cursor.fetchone()["cnt"] == 0:
        sample_certs = [
            ("CCI-2025-0101", "Karthik R", "Full Stack Web Development", "3 Months", "2025-01-15", "Distinction (A+)", "Valid", "Verified and issued by Career Connext International Skill Academy."),
            ("CCI-2025-0102", "Priya Dharshini S", "Python Programming & Data Analytics", "2 Months", "2025-02-10", "First Class (A)", "Valid", "Verified and issued by Career Connext International Skill Academy."),
            ("CCI-2025-0103", "Vignesh Kumar M", "DCA & Tally Prime with GST", "2 Months", "2025-02-28", "First Class with Distinction", "Valid", "Verified and issued by Career Connext International Skill Academy.")
        ]
        for cert in sample_certs:
            cursor.execute(
                "INSERT INTO certificates (cert_number, student_name, course_name, duration, issue_date, grade_percentage, verification_status, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                cert
            )

    # Initial Demo Enquiries (if empty)
    cursor.execute("SELECT COUNT(*) as cnt FROM enquiries")
    if cursor.fetchone()["cnt"] == 0:
        sample_enquiries = [
            ("Suresh Kumar", "9876543210", "suresh@example.com", "Full Stack Web Development", "Interested in upcoming weekend batch in Salem / Mecheri.", "New", "Needs callback on Saturday"),
            ("Anitha M", "9845123456", "anitha.m@example.com", "Spoken English & Communication Mastery", "Want morning batch timing details.", "Contacted", "Called on 12th Aug, requested brochure")
        ]
        for enq in sample_enquiries:
            cursor.execute(
                "INSERT INTO enquiries (full_name, mobile, email, course_interest, message, status, admin_notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                enq
            )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
