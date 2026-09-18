# Celestial Campus: Student Achievement Verification & Showcase Platform
> **Digital Portfolio + College Leaderboard System**

A modern web application built with **Flask, SQLite, Bootstrap 5, Vanilla JavaScript, Chart.js, and ReportLab**. The platform allows students to upload their co-curricular and academic honors (hackathons, research publications, internships, sports, cultural feats, certifications), while faculty and administrators verify, remark, score, and showcase them across campus.

---

## 🌟 Key Features

### 👨‍🎓 1. Student Portal
- **Account Registration & Authentication**: Role-based access control with secure password hashing (`Werkzeug`).
- **Achievement Submission**: Upload certificates with title, issuing authority, issue date, category, credential ID, external URL, description, and proof document (PDF / PNG / JPG / WEBP).
- **Submissions Management**: Track submission status (`Approved`, `Pending`, `Rejected`) with live badges and read faculty verification remarks.
- **Edit / Delete Before Approval**: Modify or delete pending items, or revise and resubmit rejected items based on faculty feedback.
- **Verified Portfolio PDF Export**: One-click generation of an official institutional achievement transcript powered by `ReportLab`, complete with college header, student roll number, summary table, and digital verification token.

### 👩‍🏫 2. Faculty & Admin Verification Portal
- **Review Queue**: Real-time queue of pending submissions filterable by department, category, or search keywords.
- **In-Browser Document Inspector**: Instant modal preview supporting both PDF documents and high-resolution certificate images without downloading.
- **One-Click Approval / Rejection**: Approve certificates (automatically crediting category points to the student) or reject with explanatory remarks for the student.
- **All-Submissions Audit Log**: Comprehensive institutional database of all historical records across all departments.
- **Category & Points Weight Manager**: Configure scoring weightage per category (e.g. Hackathons: +25 pts, Research: +30 pts, Internships: +20 pts, Sports: +15 pts, Cultural: +10 pts).
- **Institutional Analytics**: Visual metrics powered by `Chart.js` for department-wise achievements, category breakdown, and verification success ratios.

### 🌐 3. Public / Guest Showcase & Leaderboard
- **Public Showcase Wall**: Searchable and filterable gallery of approved achievements across departments, categories, and years.
- **Campus Leaderboard**: Gamified campus rankings with an interactive top-3 podium (Gold 👑, Silver, Bronze) and complete table of student standings.
- **Public Student Portfolios**: Shareable URL (`/portfolio/<student_id>`) showcasing verified student credentials.

---

## 🏗️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.14, Flask 3.1, Flask-SQLAlchemy, Flask-Login |
| **Database** | SQLite (Dev) / Architecture supports instant switch to MySQL |
| **PDF Engine** | ReportLab 5.0 (High-resolution vector typography and layouts) |
| **Frontend** | HTML5, CSS3, Bootstrap 5.3.3, Bootstrap Icons |
| **Interactive JS**| Vanilla JavaScript (Modal previews, dynamic filters, notifications) |
| **Analytics** | Chart.js 4.4 |
| **Storage** | Local `/static/uploads/` (Cloudinary / AWS S3 ready) |

---

## 🗄️ Database Architecture

### `users`
- `id` (INTEGER, Primary Key)
- `name` (VARCHAR)
- `email` (VARCHAR, Unique, Indexed)
- `password_hash` (VARCHAR)
- `role` (`student`, `faculty`, `admin`)
- `department` (VARCHAR)
- `student_id_no` (VARCHAR)
- `bio` (TEXT)
- `created_at` (DATETIME)

### `categories`
- `id` (INTEGER, Primary Key)
- `name` (VARCHAR, Unique)
- `description` (VARCHAR)
- `points_weight` (INTEGER) — *Configurable points awarded per certificate*
- `icon` (VARCHAR)

### `certificates`
- `id` (INTEGER, Primary Key)
- `student_id` (INTEGER, ForeignKey -> users.id)
- `category_id` (INTEGER, ForeignKey -> categories.id)
- `title` (VARCHAR)
- `issuing_org` (VARCHAR)
- `issue_date` (DATE)
- `credential_id` (VARCHAR)
- `credential_url` (VARCHAR)
- `file_path` (VARCHAR)
- `file_type` (`pdf`, `image`)
- `description` (TEXT)
- `status` (`Pending`, `Approved`, `Rejected`)
- `admin_remarks` (TEXT)
- `verified_by_id` (INTEGER, ForeignKey -> users.id)
- `verified_at` (DATETIME)
- `created_at`, `updated_at` (DATETIME)

### `notifications`
- `id` (INTEGER, Primary Key)
- `user_id` (INTEGER, ForeignKey -> users.id)
- `title` (VARCHAR)
- `message` (TEXT)
- `is_read` (BOOLEAN)
- `link` (VARCHAR)
- `created_at` (DATETIME)

---

## 🚀 Quickstart & Setup Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Initial Database with Sample Data
Populates categories, demo accounts, and sample certificates across departments:
```bash
python seed_data.py
```

### 3. Run the Development Server
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Purpose |
|---|---|---|---|
| **Admin** | `admin@college.edu` | `Admin@123` | Institutional oversight, category management, approvals |
| **Faculty** | `faculty.cs@college.edu` | `Faculty@123` | Review queue, verification with remarks |
| **Student** | `aarav@student.edu` | `Student@123` | Submissions, portfolio view, PDF export |
| **Student** | `priya@student.edu` | `Student@123` | High-scoring student on leaderboard |

*(Note: The login page includes 1-click autofill buttons for these accounts for rapid testing!)*

---

## 🔄 Production Readiness: Switching to MySQL
To transition from SQLite to MySQL in a production deployment:
1. Install the MySQL driver:
   ```bash
   pip install pymysql cryptography
   ```
2. Set the `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="mysql+pymysql://user:password@host:3306/celestial_db"
   ```
   No changes to model code or SQL queries are required thanks to the SQLAlchemy ORM abstraction!
