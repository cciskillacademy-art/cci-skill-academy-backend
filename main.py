import os
import random
import time
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from database import get_db, init_db, hash_password

# Initialize Database on startup
init_db()

app = FastAPI(
    title="CCI Skill Academy Backend API",
    description="Official Backend, Admin Portal, Certificate Verification and OTP Security for CCI Skill Academy",
    version="1.2.0"
)

# Enable CORS for frontend website integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedded Web Templates (Zero External Dependency)
ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CCI Skill Academy - Admin Management Portal</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#eef2ff',
                            100: '#e0e7ff',
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca',
                            900: '#312e81',
                        }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        [x-cloak] { display: none !important; }
        .tab-active {
            background-color: #4f46e5;
            color: white !important;
        }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans antialiased flex flex-col">

    <!-- LOGIN OVERLAY (Shows when not authenticated) -->
    <div id="loginModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-md p-8 rounded-2xl shadow-2xl">
            <div class="text-center mb-6">
                <div class="w-16 h-16 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-brand-500/30">
                    <i class="fa-solid fa-graduation-cap text-3xl text-white"></i>
                </div>
                <h2 class="text-2xl font-bold text-white">CCI Skill Academy</h2>
                <p class="text-sm text-slate-400">Admin Portal Sign In</p>
            </div>

            <form id="loginForm" onsubmit="handleLogin(event)" class="space-y-4">
                <div id="loginError" class="hidden p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-xs"></div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Username</label>
                    <div class="relative">
                        <i class="fa-solid fa-user absolute left-3 top-3.5 text-slate-400 text-sm"></i>
                        <input type="text" id="loginUsername" required placeholder="Enter username" autocomplete="off"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm">
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Password</label>
                    <div class="relative">
                        <i class="fa-solid fa-lock absolute left-3 top-3.5 text-slate-400 text-sm"></i>
                        <input type="password" id="loginPassword" required placeholder="Enter password" autocomplete="new-password"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white focus:outline-none focus:border-brand-500 text-sm">
                    </div>
                </div>
                <button type="submit" id="loginBtn"
                    class="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold py-3 rounded-xl transition duration-200 shadow-lg shadow-brand-500/25 flex items-center justify-center">
                    <span>Sign In to Dashboard</span>
                </button>
                <div class="text-center pt-2">
                    <button type="button" onclick="openOtpModal()" class="text-xs text-brand-400 hover:text-brand-300 font-semibold hover:underline flex items-center justify-center gap-1.5 mx-auto">
                        <i class="fa-solid fa-shield-halved text-amber-400"></i> Forgot / Change Password via OTP
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- OTP PASSWORD RESET MODAL -->
    <div id="otpModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-md p-6 rounded-2xl shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <i class="fa-solid fa-key text-amber-400"></i> Security OTP Password Reset
                </h3>
                <button onclick="closeModal('otpModal')" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            
            <p class="text-xs text-slate-300 mb-4 leading-relaxed">
                For high security, a 6-digit OTP will be generated for <strong class="text-brand-400">cciskillacademy@gmail.com</strong>.
            </p>

            <div id="otpAlert" class="hidden p-3 rounded-xl text-xs mb-3 font-medium"></div>

            <!-- Step 1: Send OTP -->
            <div id="otpStep1" class="space-y-3">
                <button type="button" onclick="sendOtpCode()" id="sendOtpBtn"
                    class="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-2.5 rounded-xl text-xs transition flex items-center justify-center gap-2">
                    <i class="fa-solid fa-paper-plane"></i>
                    <span>Send 6-Digit OTP to cciskillacademy@gmail.com</span>
                </button>
            </div>

            <!-- Step 2: Verify & Reset -->
            <form id="otpStep2" onsubmit="verifyOtpAndReset(event)" class="space-y-3 hidden">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Enter 6-Digit OTP Code *</label>
                    <input type="text" id="otpInput" required maxlength="6" placeholder="e.g. 748291"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-center text-base font-bold font-mono tracking-widest text-amber-400 focus:outline-none focus:border-amber-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">New Username</label>
                    <input type="text" id="otpNewUser" value="admin" required
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">New Password * (Min 6 chars)</label>
                    <input type="password" id="otpNewPass" required minlength="6" placeholder="Enter new strong password"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>

                <div class="flex justify-end gap-2 pt-2">
                    <button type="button" onclick="closeModal('otpModal')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-medium">Cancel</button>
                    <button type="submit" id="resetPassBtn" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-xs font-semibold text-white flex items-center gap-1.5">
                        <i class="fa-solid fa-lock"></i>
                        <span>Verify & Change Password</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- TOP NAVIGATION BAR -->
    <header class="bg-slate-800/90 backdrop-blur-md border-b border-slate-700 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-brand-500/20">
                        <i class="fa-solid fa-graduation-cap text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-base font-bold text-white leading-tight">CCI Skill Academy</h1>
                        <span class="text-xs text-brand-400 font-medium tracking-wide">ADMIN MANAGEMENT PORTAL</span>
                    </div>
                </div>

                <!-- Right Actions -->
                <div class="flex items-center gap-3">
                    <button onclick="openOtpModal()" class="hidden sm:inline-flex items-center gap-1.5 text-xs text-amber-300 hover:text-amber-200 bg-amber-950/40 hover:bg-amber-900/40 px-3 py-1.5 rounded-lg border border-amber-800/50 transition">
                        <i class="fa-solid fa-key"></i> Change Password
                    </button>
                    <a href="/verify" target="_blank" class="hidden sm:inline-flex items-center gap-2 text-xs text-slate-300 hover:text-white bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-600 transition">
                        <i class="fa-solid fa-external-link text-emerald-400"></i> Open Verify Portal
                    </a>
                    <a href="/docs" target="_blank" class="hidden sm:inline-flex items-center gap-2 text-xs text-slate-300 hover:text-white bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-600 transition">
                        <i class="fa-solid fa-code text-amber-400"></i> API Docs
                    </a>
                    <button onclick="logout()" class="flex items-center gap-2 text-xs text-red-400 hover:text-red-300 bg-red-950/40 hover:bg-red-900/40 px-3 py-1.5 rounded-lg border border-red-800/50 transition">
                        <i class="fa-solid fa-right-from-bracket"></i> Logout
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- MAIN APP CONTAINER -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full flex flex-col">

        <!-- TAB NAVIGATION -->
        <div class="flex flex-wrap gap-2 p-1.5 bg-slate-800 border border-slate-700 rounded-xl mb-6">
            <button onclick="switchTab('dashboard')" id="tabBtn-dashboard" class="tab-active flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white">
                <i class="fa-solid fa-gauge-high"></i> Dashboard
            </button>
            <button onclick="switchTab('enquiries')" id="tabBtn-enquiries" class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white">
                <i class="fa-solid fa-users"></i> Enquiries & Admissions <span id="badgeNewEnquiries" class="hidden ml-1 px-2 py-0.5 text-xs bg-red-500 text-white rounded-full font-bold">0</span>
            </button>
            <button onclick="switchTab('certificates')" id="tabBtn-certificates" class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white">
                <i class="fa-solid fa-award"></i> Certificate Registry
            </button>
            <button onclick="switchTab('courses')" id="tabBtn-courses" class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white">
                <i class="fa-solid fa-book-open"></i> Courses & Batches
            </button>
        </div>

        <!-- ================= TAB 1: DASHBOARD OVERVIEW ================= -->
        <div id="tabContent-dashboard" class="space-y-6">
            <!-- Stat Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="bg-slate-800 border border-slate-700 p-5 rounded-2xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Enquiries</span>
                        <div class="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                            <i class="fa-solid fa-user-group text-lg"></i>
                        </div>
                    </div>
                    <div id="statTotalEnquiries" class="text-2xl font-bold text-white">0</div>
                    <p class="text-xs text-slate-400 mt-1">Student admission leads</p>
                </div>

                <div class="bg-slate-800 border border-slate-700 p-5 rounded-2xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">New / Pending</span>
                        <div class="w-9 h-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
                            <i class="fa-solid fa-bell text-lg"></i>
                        </div>
                    </div>
                    <div id="statNewEnquiries" class="text-2xl font-bold text-amber-400">0</div>
                    <p class="text-xs text-slate-400 mt-1">Awaiting callback/action</p>
                </div>

                <div class="bg-slate-800 border border-slate-700 p-5 rounded-2xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Certificates Issued</span>
                        <div class="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                            <i class="fa-solid fa-certificate text-lg"></i>
                        </div>
                    </div>
                    <div id="statTotalCertificates" class="text-2xl font-bold text-emerald-400">0</div>
                    <p class="text-xs text-slate-400 mt-1">Verified on online portal</p>
                </div>

                <div class="bg-slate-800 border border-slate-700 p-5 rounded-2xl">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Courses</span>
                        <div class="w-9 h-9 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center">
                            <i class="fa-solid fa-layer-group text-lg"></i>
                        </div>
                    </div>
                    <div id="statActiveCourses" class="text-2xl font-bold text-sky-400">0</div>
                    <p class="text-xs text-slate-400 mt-1">Displayed on catalog</p>
                </div>
            </div>

            <!-- Recent Enquiries Widget -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-clock-rotate-left text-brand-400"></i> Recent Enquiries
                    </h3>
                    <button onclick="switchTab('enquiries')" class="text-xs text-brand-400 hover:text-brand-300 font-semibold">View All &rarr;</button>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="text-xs text-slate-400 uppercase bg-slate-900/60 rounded-xl">
                            <tr>
                                <th class="py-3 px-4 rounded-l-lg">Student Name</th>
                                <th class="py-3 px-4">Mobile</th>
                                <th class="py-3 px-4">Course Interest</th>
                                <th class="py-3 px-4">Status</th>
                                <th class="py-3 px-4 rounded-r-lg">Date</th>
                            </tr>
                        </thead>
                        <tbody id="recentEnquiriesTable" class="divide-y divide-slate-700/50">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ================= TAB 2: ENQUIRIES & LEADS ================= -->
        <div id="tabContent-enquiries" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-800 p-4 rounded-2xl border border-slate-700">
                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-xs text-slate-400 font-semibold uppercase">Filter by Status:</span>
                    <button onclick="loadEnquiries('All')" class="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-xs rounded-lg font-medium">All</button>
                    <button onclick="loadEnquiries('New')" class="px-3 py-1 bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 text-xs rounded-lg font-medium">New</button>
                    <button onclick="loadEnquiries('Contacted')" class="px-3 py-1 bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 text-xs rounded-lg font-medium">Contacted</button>
                    <button onclick="loadEnquiries('Enrolled')" class="px-3 py-1 bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 text-xs rounded-lg font-medium">Enrolled</button>
                    <button onclick="loadEnquiries('Closed')" class="px-3 py-1 bg-slate-700/50 text-slate-400 hover:bg-slate-700 text-xs rounded-lg font-medium">Closed</button>
                </div>
                <div class="w-full sm:w-auto">
                    <button onclick="openNewEnquiryModal()" class="w-full sm:w-auto bg-brand-600 hover:bg-brand-500 text-white text-xs px-4 py-2 rounded-xl font-semibold flex items-center justify-center gap-2">
                        <i class="fa-solid fa-plus"></i> Add Manual Enquiry
                    </button>
                </div>
            </div>

            <!-- Enquiries Table -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="text-xs text-slate-400 uppercase bg-slate-900/80">
                            <tr>
                                <th class="py-3 px-4">#</th>
                                <th class="py-3 px-4">Student</th>
                                <th class="py-3 px-4">Mobile & Email</th>
                                <th class="py-3 px-4">Course Interest</th>
                                <th class="py-3 px-4">Message / Notes</th>
                                <th class="py-3 px-4">Status</th>
                                <th class="py-3 px-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="allEnquiriesTable" class="divide-y divide-slate-700">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ================= TAB 3: CERTIFICATE REGISTRY ================= -->
        <div id="tabContent-certificates" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-800 p-4 rounded-2xl border border-slate-700">
                <div class="relative w-full sm:w-80">
                    <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-400 text-xs"></i>
                    <input type="text" id="searchCertInput" oninput="filterCertificates()" placeholder="Search by name or cert number..."
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>
                <button onclick="openNewCertModal()" class="w-full sm:w-auto bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-4 py-2.5 rounded-xl font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20">
                    <i class="fa-solid fa-plus"></i> Issue New Certificate
                </button>
            </div>

            <!-- Certificates Table -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm text-slate-300">
                        <thead class="text-xs text-slate-400 uppercase bg-slate-900/80">
                            <tr>
                                <th class="py-3 px-4">Cert Number</th>
                                <th class="py-3 px-4">Student Name</th>
                                <th class="py-3 px-4">Course Name</th>
                                <th class="py-3 px-4">Issue Date</th>
                                <th class="py-3 px-4">Grade / Score</th>
                                <th class="py-3 px-4">Status</th>
                                <th class="py-3 px-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="allCertificatesTable" class="divide-y divide-slate-700">
                            <!-- Populated via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ================= TAB 4: COURSES & BATCHES ================= -->
        <div id="tabContent-courses" class="hidden space-y-4">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-800 p-4 rounded-2xl border border-slate-700">
                <div>
                    <h3 class="text-sm font-bold text-white">Course Offerings</h3>
                    <p class="text-xs text-slate-400">Courses listed here are served directly to the website.</p>
                </div>
                <button onclick="openNewCourseModal()" class="w-full sm:w-auto bg-brand-600 hover:bg-brand-500 text-white text-xs px-4 py-2.5 rounded-xl font-semibold flex items-center justify-center gap-2">
                    <i class="fa-solid fa-plus"></i> Add New Course
                </button>
            </div>

            <!-- Courses Grid -->
            <div id="coursesGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Populated via JS -->
            </div>
        </div>

    </div>

    <!-- MODAL: ADD / EDIT CERTIFICATE -->
    <div id="certModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-lg p-6 rounded-2xl shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h3 id="certModalTitle" class="text-lg font-bold text-white">Issue Student Certificate</h3>
                <button onclick="closeModal('certModal')" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            <form onsubmit="saveCertificate(event)" class="space-y-3">
                <input type="hidden" id="certId">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Certificate Number *</label>
                        <input type="text" id="certNumber" required placeholder="e.g. CCI-2026-0201"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white uppercase focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Student Full Name *</label>
                        <input type="text" id="certStudentName" required placeholder="e.g. Ramesh K"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Course Name *</label>
                    <input type="text" id="certCourseName" required placeholder="e.g. Python Full Stack Development"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Duration</label>
                        <input type="text" id="certDuration" placeholder="e.g. 3 Months" value="3 Months"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Issue Date *</label>
                        <input type="date" id="certIssueDate" required
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Grade / Score</label>
                        <input type="text" id="certGrade" placeholder="e.g. First Class (A+)" value="First Class"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Remarks / Note</label>
                    <textarea id="certRemarks" rows="2"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">Verified and issued by Career Connext International Skill Academy.</textarea>
                </div>

                <div class="flex justify-end gap-2 pt-3">
                    <button type="button" onclick="closeModal('certModal')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-medium">Cancel</button>
                    <button type="submit" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-xs font-semibold text-white">Save Certificate</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL: ADD / EDIT COURSE -->
    <div id="courseModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-lg p-6 rounded-2xl shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h3 id="courseModalTitle" class="text-lg font-bold text-white">Add New Course</h3>
                <button onclick="closeModal('courseModal')" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            <form onsubmit="saveCourse(event)" class="space-y-3">
                <input type="hidden" id="courseId">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Course Title *</label>
                    <input type="text" id="courseTitle" required placeholder="e.g. Master in Python Programming"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Category *</label>
                        <input type="text" id="courseCategory" required placeholder="e.g. Software / Language"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Duration *</label>
                        <input type="text" id="courseDuration" required placeholder="e.g. 2 Months"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Course Fee</label>
                        <input type="text" id="courseFee" placeholder="e.g. Rs. 8,000"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Description</label>
                    <textarea id="courseDesc" rows="2" placeholder="Course overview and career opportunities..."
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"></textarea>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Syllabus Highlights (comma separated)</label>
                    <input type="text" id="courseSyllabus" placeholder="e.g. Basics, Advanced SQL, Live Projects, Interview Prep"
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                </div>

                <div class="flex justify-end gap-2 pt-3">
                    <button type="button" onclick="closeModal('courseModal')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-medium">Cancel</button>
                    <button type="submit" class="px-5 py-2 bg-brand-600 hover:bg-brand-500 rounded-xl text-xs font-semibold text-white">Save Course</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL: UPDATE ENQUIRY STATUS / NOTES -->
    <div id="enquiryModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-md p-6 rounded-2xl shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-white">Update Lead Status & Notes</h3>
                <button onclick="closeModal('enquiryModal')" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            <form onsubmit="saveEnquiryUpdate(event)" class="space-y-4">
                <input type="hidden" id="editEnquiryId">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Lead Status</label>
                    <select id="editEnquiryStatus" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                        <option value="New">New (Uncontacted)</option>
                        <option value="Contacted">Contacted / In Discussion</option>
                        <option value="Enrolled">Enrolled in Batch</option>
                        <option value="Closed">Closed / Not Interested</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Admin Notes / Remarks</label>
                    <textarea id="editEnquiryNotes" rows="3" placeholder="e.g. Student requested weekend morning batch, called on 15th..."
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"></textarea>
                </div>
                <div class="flex justify-end gap-2 pt-2">
                    <button type="button" onclick="closeModal('enquiryModal')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-medium">Cancel</button>
                    <button type="submit" class="px-5 py-2 bg-brand-600 hover:bg-brand-500 rounded-xl text-xs font-semibold text-white">Update Lead</button>
                </div>
            </form>
        </div>
    </div>

    <!-- MODAL: ADD MANUAL ENQUIRY -->
    <div id="manualEnquiryModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 hidden">
        <div class="bg-slate-800 border border-slate-700 w-full max-w-lg p-6 rounded-2xl shadow-2xl">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <i class="fa-solid fa-user-plus text-brand-400"></i> Add Student Enquiry
                </h3>
                <button onclick="closeModal('manualEnquiryModal')" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark text-lg"></i></button>
            </div>
            <form onsubmit="saveManualEnquiry(event)" class="space-y-3">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Student Full Name *</label>
                        <input type="text" id="manualEnqName" required placeholder="e.g. Anand Kumar"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Mobile Number *</label>
                        <input type="text" id="manualEnqMobile" required placeholder="e.g. 9876543210"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Email Address</label>
                        <input type="email" id="manualEnqEmail" placeholder="e.g. student@gmail.com"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-300 mb-1">Course of Interest *</label>
                        <input type="text" id="manualEnqCourse" required placeholder="e.g. Python Programming / Tally"
                            class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1">Notes / Message</label>
                    <textarea id="manualEnqMessage" rows="2" placeholder="e.g. Walk-in enquiry at Salem center, interested in weekend batch..."
                        class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-brand-500"></textarea>
                </div>

                <div class="flex justify-end gap-2 pt-3">
                    <button type="button" onclick="closeModal('manualEnquiryModal')" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-xl text-xs font-medium">Cancel</button>
                    <button type="submit" class="px-5 py-2 bg-brand-600 hover:bg-brand-500 rounded-xl text-xs font-semibold text-white">Save Enquiry</button>
                </div>
            </form>
        </div>
    </div>

    <!-- JAVASCRIPT LOGIC -->
    <script>
        let authToken = localStorage.getItem("cci_admin_token");
        let allCertificates = [];

        window.addEventListener("DOMContentLoaded", () => {
            checkAuth();
            loadDashboard();
        });

        // ================= SECURITY OTP PASSWORD RESET =================
        function openOtpModal() {
            document.getElementById("otpAlert").classList.add("hidden");
            document.getElementById("otpStep1").classList.remove("hidden");
            document.getElementById("otpStep2").classList.add("hidden");
            document.getElementById("otpInput").value = "";
            document.getElementById("otpNewPass").value = "";
            document.getElementById("otpModal").classList.remove("hidden");
        }

        async function sendOtpCode() {
            const btn = document.getElementById("sendOtpBtn");
            const alertBox = document.getElementById("otpAlert");
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Generating & Sending OTP...</span>`;

            try {
                const res = await fetch("/api/auth/send-otp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email: "cciskillacademy@gmail.com" })
                });
                const data = await res.json();

                alertBox.className = "p-3 rounded-xl text-xs mb-3 font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 block";
                alertBox.innerHTML = `<i class="fa-solid fa-circle-check mr-1"></i> ${data.message || "OTP Sent to cciskillacademy@gmail.com"}`;
                
                document.getElementById("otpStep1").classList.add("hidden");
                document.getElementById("otpStep2").classList.remove("hidden");
            } catch (err) {
                alertBox.className = "p-3 rounded-xl text-xs mb-3 font-semibold bg-red-500/20 text-red-300 border border-red-500/40 block";
                alertBox.innerText = "Error sending OTP. Please try again.";
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>Send 6-Digit OTP to cciskillacademy@gmail.com</span>`;
            }
        }

        async function verifyOtpAndReset(e) {
            e.preventDefault();
            const btn = document.getElementById("resetPassBtn");
            const alertBox = document.getElementById("otpAlert");
            const otp = document.getElementById("otpInput").value.trim();
            const new_username = document.getElementById("otpNewUser").value.trim();
            const new_password = document.getElementById("otpNewPass").value;

            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Verifying...</span>`;

            try {
                const res = await fetch("/api/auth/verify-otp-and-reset", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ otp, new_username, new_password })
                });
                const data = await res.json();

                if (res.ok && data.success) {
                    alertBox.className = "p-3 rounded-xl text-xs mb-3 font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 block";
                    alertBox.innerHTML = `<i class="fa-solid fa-circle-check mr-1"></i> ${data.message}`;
                    setTimeout(() => {
                        closeModal("otpModal");
                        logout();
                        alert("Password successfully changed! Please sign in with your new password.");
                    }, 1500);
                } else {
                    alertBox.className = "p-3 rounded-xl text-xs mb-3 font-semibold bg-red-500/20 text-red-300 border border-red-500/40 block";
                    alertBox.innerText = data.detail || "Invalid OTP code";
                }
            } catch (err) {
                alertBox.className = "p-3 rounded-xl text-xs mb-3 font-semibold bg-red-500/20 text-red-300 border border-red-500/40 block";
                alertBox.innerText = "Error verifying OTP";
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-lock"></i> <span>Verify & Change Password</span>`;
            }
        }

        function openNewEnquiryModal() {
            document.getElementById("manualEnqName").value = "";
            document.getElementById("manualEnqMobile").value = "";
            document.getElementById("manualEnqEmail").value = "";
            document.getElementById("manualEnqCourse").value = "";
            document.getElementById("manualEnqMessage").value = "";
            document.getElementById("manualEnquiryModal").classList.remove("hidden");
        }

        async function saveManualEnquiry(e) {
            e.preventDefault();
            const payload = {
                full_name: document.getElementById("manualEnqName").value,
                mobile: document.getElementById("manualEnqMobile").value,
                email: document.getElementById("manualEnqEmail").value,
                course_interest: document.getElementById("manualEnqCourse").value,
                message: document.getElementById("manualEnqMessage").value
            };

            const res = await fetch("/api/enquiries", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                closeModal("manualEnquiryModal");
                loadEnquiries();
                loadDashboard();
            } else {
                alert("Error saving enquiry");
            }
        }

        function checkAuth() {
            if (!authToken) {
                document.getElementById("loginModal").classList.remove("hidden");
            } else {
                document.getElementById("loginModal").classList.add("hidden");
            }
        }

        async function handleLogin(e) {
            e.preventDefault();
            const u = document.getElementById("loginUsername").value;
            const p = document.getElementById("loginPassword").value;
            const err = document.getElementById("loginError");
            err.classList.add("hidden");

            try {
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await res.json();
                if (res.ok && data.token) {
                    authToken = data.token;
                    localStorage.setItem("cci_admin_token", authToken);
                    document.getElementById("loginModal").classList.add("hidden");
                    loadDashboard();
                } else {
                    err.innerText = data.detail || "Invalid login credentials";
                    err.classList.remove("hidden");
                }
            } catch (error) {
                err.innerText = "Error connecting to server";
                err.classList.remove("hidden");
            }
        }

        function logout() {
            localStorage.removeItem("cci_admin_token");
            authToken = null;
            document.getElementById("loginModal").classList.remove("hidden");
        }

        function switchTab(tab) {
            ['dashboard', 'enquiries', 'certificates', 'courses'].forEach(t => {
                document.getElementById(`tabContent-${t}`).classList.add("hidden");
                document.getElementById(`tabBtn-${t}`).classList.remove("tab-active");
            });

            document.getElementById(`tabContent-${tab}`).classList.remove("hidden");
            document.getElementById(`tabBtn-${tab}`).classList.add("tab-active");

            if (tab === 'dashboard') loadDashboard();
            if (tab === 'enquiries') loadEnquiries('All');
            if (tab === 'certificates') loadCertificates();
            if (tab === 'courses') loadCourses();
        }

        // ================= API CALLS =================

        async function loadDashboard() {
            try {
                const res = await fetch("/api/dashboard/stats", {
                    headers: { "Authorization": `Bearer ${authToken}` }
                });
                if (!res.ok) { logout(); return; }
                const data = await res.json();
                
                document.getElementById("statTotalEnquiries").innerText = data.stats.total_enquiries;
                document.getElementById("statNewEnquiries").innerText = data.stats.new_enquiries;
                document.getElementById("statTotalCertificates").innerText = data.stats.total_certificates;
                document.getElementById("statActiveCourses").innerText = data.stats.active_courses;

                if (data.stats.new_enquiries > 0) {
                    const badge = document.getElementById("badgeNewEnquiries");
                    badge.innerText = data.stats.new_enquiries;
                    badge.classList.remove("hidden");
                }

                // Recent table
                const tbody = document.getElementById("recentEnquiriesTable");
                tbody.innerHTML = "";
                if (data.recent_enquiries.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-500">No enquiries received yet.</td></tr>`;
                    return;
                }

                data.recent_enquiries.forEach(enq => {
                    const statusColor = enq.status === 'New' ? 'bg-amber-500/20 text-amber-300' :
                                      enq.status === 'Enrolled' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300';
                    tbody.innerHTML += `
                        <tr class="hover:bg-slate-750">
                            <td class="py-3 px-4 font-semibold text-white">${enq.full_name}</td>
                            <td class="py-3 px-4 font-mono text-xs">${enq.mobile}</td>
                            <td class="py-3 px-4">${enq.course_interest}</td>
                            <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-xs font-semibold ${statusColor}">${enq.status}</span></td>
                            <td class="py-3 px-4 text-xs text-slate-400">${enq.created_at.split(' ')[0]}</td>
                        </tr>
                    `;
                });
            } catch (e) {
                console.error(e);
            }
        }

        async function loadEnquiries(filterStatus = 'All') {
            try {
                const url = filterStatus === 'All' ? '/api/admin/enquiries' : `/api/admin/enquiries?status=${filterStatus}`;
                const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
                const enquiries = await res.json();

                const tbody = document.getElementById("allEnquiriesTable");
                tbody.innerHTML = "";
                if (enquiries.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-500">No enquiries found.</td></tr>`;
                    return;
                }

                enquiries.forEach((enq, idx) => {
                    const statusColor = enq.status === 'New' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                                      enq.status === 'Contacted' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                                      enq.status === 'Enrolled' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-700 text-slate-300';
                    tbody.innerHTML += `
                        <tr class="hover:bg-slate-750">
                            <td class="py-3 px-4 text-slate-400 text-xs">${idx + 1}</td>
                            <td class="py-3 px-4">
                                <div class="font-bold text-white">${enq.full_name}</div>
                                <div class="text-xs text-slate-400">${enq.created_at}</div>
                            </td>
                            <td class="py-3 px-4">
                                <div class="font-mono text-xs text-emerald-400"><i class="fa-solid fa-phone text-[10px] mr-1"></i>${enq.mobile}</div>
                                <div class="text-xs text-slate-400">${enq.email || '-'}</div>
                            </td>
                            <td class="py-3 px-4 font-medium text-indigo-300">${enq.course_interest}</td>
                            <td class="py-3 px-4 text-xs">
                                <div class="text-slate-200">${enq.message || '-'}</div>
                                ${enq.admin_notes ? `<div class="text-amber-400 text-[11px] mt-1"><i class="fa-solid fa-note-sticky mr-1"></i>${enq.admin_notes}</div>` : ''}
                            </td>
                            <td class="py-3 px-4"><span class="px-2.5 py-1 rounded-full text-xs font-semibold ${statusColor}">${enq.status}</span></td>
                            <td class="py-3 px-4 text-right space-x-2">
                                <button onclick="openEnquiryModal(${enq.id}, '${enq.status}', '${(enq.admin_notes || '').replace(/'/g, "\\'")}')" class="p-1.5 bg-slate-700 hover:bg-slate-600 text-brand-300 rounded-lg text-xs" title="Update Status">
                                    <i class="fa-solid fa-pen-to-square"></i>
                                </button>
                                <button onclick="deleteEnquiry(${enq.id})" class="p-1.5 bg-red-950/50 hover:bg-red-900/60 text-red-400 rounded-lg text-xs" title="Delete">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
            } catch (e) {
                console.error(e);
            }
        }

        function openEnquiryModal(id, status, notes) {
            document.getElementById("editEnquiryId").value = id;
            document.getElementById("editEnquiryStatus").value = status;
            document.getElementById("editEnquiryNotes").value = notes;
            document.getElementById("enquiryModal").classList.remove("hidden");
        }

        async function saveEnquiryUpdate(e) {
            e.preventDefault();
            const id = document.getElementById("editEnquiryId").value;
            const status = document.getElementById("editEnquiryStatus").value;
            const admin_notes = document.getElementById("editEnquiryNotes").value;

            await fetch(`/api/admin/enquiries/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
                body: JSON.stringify({ status, admin_notes })
            });
            closeModal("enquiryModal");
            loadEnquiries();
            loadDashboard();
        }

        async function deleteEnquiry(id) {
            if (!confirm("Are you sure you want to delete this enquiry?")) return;
            await fetch(`/api/admin/enquiries/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            loadEnquiries();
            loadDashboard();
        }

        // ================= CERTIFICATES =================

        async function loadCertificates() {
            try {
                const res = await fetch("/api/admin/certificates", { headers: { "Authorization": `Bearer ${authToken}` } });
                allCertificates = await res.json();
                renderCertificatesTable(allCertificates);
            } catch (e) {
                console.error(e);
            }
        }

        function filterCertificates() {
            const q = document.getElementById("searchCertInput").value.toLowerCase();
            const filtered = allCertificates.filter(c => 
                c.student_name.toLowerCase().includes(q) || 
                c.cert_number.toLowerCase().includes(q) || 
                c.course_name.toLowerCase().includes(q)
            );
            renderCertificatesTable(filtered);
        }

        function renderCertificatesTable(certs) {
            const tbody = document.getElementById("allCertificatesTable");
            tbody.innerHTML = "";
            if (certs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-500">No certificates registered yet.</td></tr>`;
                return;
            }

            certs.forEach(cert => {
                tbody.innerHTML += `
                    <tr class="hover:bg-slate-750">
                        <td class="py-3 px-4 font-mono font-bold text-amber-400 text-xs">${cert.cert_number}</td>
                        <td class="py-3 px-4 font-bold text-white">${cert.student_name}</td>
                        <td class="py-3 px-4 text-indigo-300 text-xs font-medium">${cert.course_name}</td>
                        <td class="py-3 px-4 text-xs text-slate-400">${cert.issue_date}</td>
                        <td class="py-3 px-4 text-xs font-semibold text-emerald-400">${cert.grade_percentage}</td>
                        <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300">${cert.verification_status}</span></td>
                        <td class="py-3 px-4 text-right space-x-2">
                            <a href="/verify?id=${encodeURIComponent(cert.cert_number)}" target="_blank" class="p-1.5 bg-slate-700 hover:bg-slate-600 text-emerald-400 rounded-lg text-xs inline-block" title="Verify Online">
                                <i class="fa-solid fa-eye"></i>
                            </a>
                            <button onclick="deleteCertificate(${cert.id})" class="p-1.5 bg-red-950/50 hover:bg-red-900/60 text-red-400 rounded-lg text-xs" title="Delete">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                `;
            });
        }

        function openNewCertModal() {
            document.getElementById("certId").value = "";
            document.getElementById("certModalTitle").innerText = "Issue New Student Certificate";
            document.getElementById("certNumber").value = "CCI-2026-" + Math.floor(1000 + Math.random() * 9000);
            document.getElementById("certStudentName").value = "";
            document.getElementById("certCourseName").value = "";
            document.getElementById("certIssueDate").value = new Date().toISOString().split('T')[0];
            document.getElementById("certModal").classList.remove("hidden");
        }

        async function saveCertificate(e) {
            e.preventDefault();
            const payload = {
                cert_number: document.getElementById("certNumber").value,
                student_name: document.getElementById("certStudentName").value,
                course_name: document.getElementById("certCourseName").value,
                duration: document.getElementById("certDuration").value,
                issue_date: document.getElementById("certIssueDate").value,
                grade_percentage: document.getElementById("certGrade").value,
                remarks: document.getElementById("certRemarks").value
            };

            const res = await fetch("/api/admin/certificates", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                closeModal("certModal");
                loadCertificates();
                loadDashboard();
            } else {
                const err = await res.json();
                alert(err.detail || "Error saving certificate");
            }
        }

        async function deleteCertificate(id) {
            if (!confirm("Are you sure you want to delete this certificate record?")) return;
            await fetch(`/api/admin/certificates/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            loadCertificates();
            loadDashboard();
        }

        // ================= COURSES =================

        async function loadCourses() {
            try {
                const res = await fetch("/api/admin/courses", { headers: { "Authorization": `Bearer ${authToken}` } });
                const courses = await res.json();

                const grid = document.getElementById("coursesGrid");
                grid.innerHTML = "";
                if (courses.length === 0) {
                    grid.innerHTML = `<div class="col-span-3 text-center py-8 text-slate-500">No courses added yet.</div>`;
                    return;
                }

                courses.forEach(c => {
                    grid.innerHTML += `
                        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-5 flex flex-col justify-between hover:border-brand-500/50 transition">
                            <div>
                                <div class="flex items-center justify-between mb-2">
                                    <span class="px-2.5 py-0.5 bg-brand-500/20 text-brand-300 text-xs font-bold rounded-lg">${c.category}</span>
                                    <span class="text-xs text-slate-400 font-mono"><i class="fa-solid fa-clock mr-1"></i>${c.duration}</span>
                                </div>
                                <h4 class="text-base font-bold text-white mb-1">${c.title}</h4>
                                <p class="text-xs text-slate-400 mb-3">${c.description || 'No description provided.'}</p>
                                ${c.syllabus ? `<div class="text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded-xl mb-3"><strong class="text-brand-400">Syllabus:</strong> ${c.syllabus}</div>` : ''}
                            </div>
                            <div class="flex items-center justify-between pt-3 border-t border-slate-700/60">
                                <span class="text-sm font-bold text-emerald-400">${c.fee || 'Contact for fee'}</span>
                                <button onclick="deleteCourse(${c.id})" class="text-red-400 hover:text-red-300 text-xs font-semibold">
                                    <i class="fa-solid fa-trash mr-1"></i> Delete
                                </button>
                            </div>
                        </div>
                    `;
                });
            } catch (e) {
                console.error(e);
            }
        }

        function openNewCourseModal() {
            document.getElementById("courseTitle").value = "";
            document.getElementById("courseCategory").value = "Software & IT";
            document.getElementById("courseDuration").value = "3 Months";
            document.getElementById("courseFee").value = "";
            document.getElementById("courseDesc").value = "";
            document.getElementById("courseSyllabus").value = "";
            document.getElementById("courseModal").classList.remove("hidden");
        }

        async function saveCourse(e) {
            e.preventDefault();
            const payload = {
                title: document.getElementById("courseTitle").value,
                category: document.getElementById("courseCategory").value,
                duration: document.getElementById("courseDuration").value,
                fee: document.getElementById("courseFee").value,
                description: document.getElementById("courseDesc").value,
                syllabus: document.getElementById("courseSyllabus").value,
                is_active: 1
            };

            await fetch("/api/admin/courses", {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
                body: JSON.stringify(payload)
            });

            closeModal("courseModal");
            loadCourses();
            loadDashboard();
        }

        async function deleteCourse(id) {
            if (!confirm("Are you sure you want to delete this course?")) return;
            await fetch(`/api/admin/courses/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            loadCourses();
            loadDashboard();
        }

        function closeModal(id) {
            document.getElementById(id).classList.add("hidden");
        }
    </script>
</body>
</html>
"""
VERIFY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate Verification - CCI Skill Academy</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#eef2ff',
                            100: '#e0e7ff',
                            500: '#6366f1',
                            600: '#4f46e5',
                            700: '#4338ca',
                            900: '#312e81',
                        }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @media print {
            body { background: white; color: black; }
            .no-print { display: none !important; }
            #certCard { border: 2px solid #333; box-shadow: none; }
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans flex flex-col justify-between">

    <!-- HEADER -->
    <header class="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 py-4 no-print">
        <div class="max-w-5xl mx-auto px-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center text-white shadow-md shadow-brand-500/20">
                    <i class="fa-solid fa-graduation-cap text-lg"></i>
                </div>
                <div>
                    <h1 class="text-base font-bold text-white leading-tight">CCI Skill Academy</h1>
                    <p class="text-xs text-slate-400">Career Connext International Skill Academy</p>
                </div>
            </div>
            <a href="https://www.cciskillacademy.com" target="_blank" class="text-xs text-slate-300 hover:text-white bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg transition">
                <i class="fa-solid fa-arrow-left mr-1"></i> Back to Main Website
            </a>
        </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="max-w-3xl mx-auto px-4 py-10 w-full flex-1">
        
        <!-- Search Box -->
        <div class="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl mb-8 no-print">
            <div class="text-center mb-6">
                <div class="inline-flex p-3 bg-emerald-500/10 text-emerald-400 rounded-2xl mb-3">
                    <i class="fa-solid fa-certificate text-3xl"></i>
                </div>
                <h2 class="text-2xl font-extrabold text-white">Online Certificate Verification</h2>
                <p class="text-xs sm:text-sm text-slate-400 mt-1">Verify credentials, courses, and student authenticity issued by CCI Skill Academy</p>
            </div>

            <form onsubmit="handleSearch(event)" class="flex flex-col sm:flex-row gap-3">
                <div class="relative flex-1">
                    <i class="fa-solid fa-barcode absolute left-3.5 top-3.5 text-slate-400"></i>
                    <input type="text" id="certInput" required placeholder="Enter Certificate Number (e.g. CCI-2025-0101)"
                        class="w-full bg-slate-950 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm text-white uppercase tracking-wider focus:outline-none focus:border-brand-500">
                </div>
                <button type="submit" id="searchBtn"
                    class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-2">
                    <i class="fa-solid fa-shield-halved"></i>
                    <span>Verify Now</span>
                </button>
            </form>
        </div>

        <!-- RESULT CONTAINER -->
        <div id="resultBox" class="hidden">
            <!-- NOT FOUND STATE -->
            <div id="notFoundCard" class="hidden bg-red-950/40 border border-red-800/60 p-6 rounded-2xl text-center">
                <div class="w-12 h-12 bg-red-500/20 text-red-400 rounded-full flex items-center justify-center mx-auto mb-3 text-xl">
                    <i class="fa-solid fa-circle-xmark"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-1">Certificate Not Found</h3>
                <p id="notResultMessage" class="text-xs text-slate-300 max-w-md mx-auto"></p>
            </div>

            <!-- SUCCESS VERIFIED CARD -->
            <div id="certCard" class="hidden bg-slate-900 border-2 border-emerald-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
                <!-- Top Badge -->
                <div class="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span>
                        <span class="text-xs font-bold text-emerald-400 tracking-wider uppercase">Authentic & Verified Record</span>
                    </div>
                    <span class="text-xs text-slate-400 font-mono" id="displayVerifiedDate"></span>
                </div>

                <div class="text-center my-4">
                    <p class="text-xs text-slate-400 uppercase tracking-widest font-semibold mb-1">This is to certify that</p>
                    <h3 id="displayStudentName" class="text-2xl sm:text-3xl font-extrabold text-white text-emerald-300 mb-2"></h3>
                    <p class="text-xs text-slate-400">has successfully completed the prescribed course of study in</p>
                    <h4 id="displayCourseName" class="text-lg sm:text-xl font-bold text-brand-400 mt-2 mb-4"></h4>
                </div>

                <!-- Info Grid -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/70 p-4 rounded-2xl border border-slate-800 my-6 text-center">
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block">Certificate ID</span>
                        <span id="displayCertNo" class="font-mono text-xs sm:text-sm font-bold text-amber-400"></span>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block">Duration</span>
                        <span id="displayDuration" class="text-xs sm:text-sm font-semibold text-white"></span>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block">Issue Date</span>
                        <span id="displayIssueDate" class="text-xs sm:text-sm font-semibold text-white"></span>
                    </div>
                    <div>
                        <span class="text-[10px] text-slate-400 uppercase font-semibold block">Grade / Class</span>
                        <span id="displayGrade" class="text-xs sm:text-sm font-bold text-emerald-400"></span>
                    </div>
                </div>

                <!-- Footer remarks & signature info -->
                <div class="border-t border-slate-800 pt-4 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-4">
                    <div>
                        <span class="font-semibold text-slate-300">Issued by:</span> Career Connext International Skill Academy
                        <div class="text-[11px] text-slate-500">Mecheri, Salem, Tamil Nadu, India</div>
                    </div>
                    <div class="no-print">
                        <button onclick="window.print()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 font-medium transition flex items-center gap-2">
                            <i class="fa-solid fa-print"></i> Print / Save Record
                        </button>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- FOOTER -->
    <footer class="border-t border-slate-800 py-6 text-center text-xs text-slate-500 no-print">
        <p>Career Connext International Skill Academy (CCI Skill Academy) &copy; 2026. All Rights Reserved.</p>
        <p class="mt-1 text-[11px]">Official Verification Portal for www.cciskillacademy.com</p>
    </footer>

    <!-- SCRIPT -->
    <script>
        window.addEventListener("DOMContentLoaded", () => {
            const urlParams = new URLSearchParams(window.location.search);
            const id = urlParams.get('id');
            if (id) {
                document.getElementById("certInput").value = id;
                verifyCert(id);
            }
        });

        function handleSearch(e) {
            e.preventDefault();
            const id = document.getElementById("certInput").value.trim();
            if (id) verifyCert(id);
        }

        async function verifyCert(certNo) {
            const resultBox = document.getElementById("resultBox");
            const notFoundCard = document.getElementById("notFoundCard");
            const certCard = document.getElementById("certCard");
            const notResultMessage = document.getElementById("notResultMessage");

            resultBox.classList.remove("hidden");
            notFoundCard.classList.add("hidden");
            certCard.classList.add("hidden");

            try {
                const res = await fetch(`/api/certificates/verify/${encodeURIComponent(certNo)}`);
                const data = await res.json();

                if (data.verified && data.data) {
                    const c = data.data;
                    document.getElementById("displayStudentName").innerText = c.student_name;
                    document.getElementById("displayCourseName").innerText = c.course_name;
                    document.getElementById("displayCertNo").innerText = c.cert_number;
                    document.getElementById("displayDuration").innerText = c.duration || "Course Completed";
                    document.getElementById("displayIssueDate").innerText = c.issue_date;
                    document.getElementById("displayGrade").innerText = c.grade_percentage || "Pass";
                    document.getElementById("displayVerifiedDate").innerText = "Verified on: " + data.verified_at;

                    certCard.classList.remove("hidden");
                } else {
                    notResultMessage.innerText = data.message || `No certificate record found matching '${certNo}'.`;
                    notFoundCard.classList.remove("hidden");
                }
            } catch (err) {
                notResultMessage.innerText = "Error communicating with the verification database.";
                notFoundCard.classList.remove("hidden");
            }
        }
    </script>
</body>
</html>
"""

ADMIN_EMAIL = "cciskillacademy@gmail.com"
ACTIVE_TOKENS = {}
OTP_STORAGE = {}  # {email: {"otp": "123456", "expires_at": timestamp}}

# ----------------- EMAIL OTP SENDER FUNCTION -----------------
def send_otp_email(to_email: str, otp_code: str) -> bool:
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"CCI Skill Academy - Your Security OTP: {otp_code}"
            msg["From"] = f"CCI Skill Academy Security <{smtp_user}>"
            msg["To"] = to_email

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #4f46e5; margin: 0;">CCI Skill Academy</h2>
                    <p style="color: #64748b; font-size: 13px; margin: 5px 0;">Career Connext International Skill Academy</p>
                </div>
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <p style="font-size: 14px; color: #334155; margin: 0 0 10px 0;">Your One-Time Password (OTP) to change/reset Admin Password is:</p>
                    <div style="font-size: 32px; font-weight: bold; letter-spacing: 6px; color: #4f46e5; margin: 10px 0;">{otp_code}</div>
                    <p style="font-size: 12px; color: #ef4444; margin: 10px 0 0 0;">This OTP is valid for 10 minutes only. Never share this code with anyone.</p>
                </div>
                <p style="font-size: 12px; color: #94a3b8; text-align: center;">If you did not request this, please ignore this email.</p>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to_email, msg.as_string())
            print(f"[+] Real OTP Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"[-] SMTP sending failed: {e}")
    
    print(f"[*] [SECURITY OTP GENERATED FOR {to_email}]: {otp_code}")
    return True


# ----------------- PYDANTIC SCHEMAS -----------------
class LoginRequest(BaseModel):
    username: str
    password: str

class SendOtpRequest(BaseModel):
    email: Optional[str] = ADMIN_EMAIL

class VerifyOtpResetRequest(BaseModel):
    otp: str
    new_username: Optional[str] = "admin"
    new_password: str

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
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in.")
    return token


# =========================================================
#                   SECURITY & OTP ROUTES
# =========================================================

@app.post("/api/auth/send-otp")
def send_otp_route(payload: SendOtpRequest):
    otp_code = str(random.randint(100000, 999999))
    expires_at = time.time() + 600

    target_email = payload.email.strip() if payload.email else ADMIN_EMAIL
    OTP_STORAGE[target_email.lower()] = {
        "otp": otp_code,
        "expires_at": expires_at
    }

    send_otp_email(target_email, otp_code)

    return {
        "success": True,
        "message": f"6-digit Security OTP has been generated for {target_email}."
    }

@app.post("/api/auth/verify-otp-and-reset")
def verify_otp_and_reset(payload: VerifyOtpResetRequest):
    target_email = ADMIN_EMAIL.lower()
    stored = OTP_STORAGE.get(target_email)

    if not stored:
        raise HTTPException(status_code=400, detail="No active OTP found. Please click 'Send OTP' first.")

    if time.time() > stored["expires_at"]:
        del OTP_STORAGE[target_email]
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")

    if stored["otp"] != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP code. Please enter the correct 6-digit OTP.")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins ORDER BY id ASC LIMIT 1")
    admin = cursor.fetchone()
    
    new_user = payload.new_username.strip() if payload.new_username else "admin"
    new_hash = hash_password(payload.new_password)

    if admin:
        cursor.execute("UPDATE admins SET username = ?, password_hash = ? WHERE id = ?", (new_user, new_hash, admin["id"]))
    else:
        cursor.execute("INSERT INTO admins (username, password_hash, role) VALUES (?, ?, 'admin')", (new_user, new_hash))
    
    conn.commit()
    conn.close()

    del OTP_STORAGE[target_email]
    ACTIVE_TOKENS.clear()

    return {
        "success": True,
        "message": f"Password changed successfully! You can now sign in with your new credentials."
    }


# =========================================================
#                   PUBLIC API ROUTES
# =========================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CCI Skill Academy Backend",
        "version": "1.2.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM admins WHERE username = ?", (payload.username.strip(),))
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

@app.get("/api/courses")
def get_public_courses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
    return ADMIN_HTML

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return ADMIN_HTML

@app.get("/verify", response_class=HTMLResponse)
def verify_page():
    return VERIFY_HTML
