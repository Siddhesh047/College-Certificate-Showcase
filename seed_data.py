import os
from datetime import date, datetime, timezone
from flask import Flask
from models import db, User, Category, Certificate, Notification
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw, ImageFont

def create_sample_files(upload_dir):
    try:
        os.makedirs(upload_dir, exist_ok=True)

        # 1. Sample PDF Certificate
        pdf_path = os.path.join(upload_dir, 'sample_hackathon_award.pdf')
        if not os.path.exists(pdf_path):
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CertTitle',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#1e3a8a'),
                alignment=1
            )
            body_style = ParagraphStyle(
                'CertBody',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=13,
                leading=18,
                alignment=1
            )
            story = [
                Spacer(1, 40),
                Paragraph("CERTIFICATE OF EXCELLENCE", title_style),
                Spacer(1, 15),
                Paragraph("This certificate is proudly awarded to the recipient for outstanding performance in the", body_style),
                Spacer(1, 10),
                Paragraph("<b>National Hackathon & Innovation Challenge 2026</b>", ParagraphStyle('Sub', parent=body_style, fontSize=16, textColor=colors.HexColor('#0284c7'))),
                Spacer(1, 15),
                Paragraph("Issued with high commendation for technical excellence, team leadership, and innovation.", body_style),
                Spacer(1, 40),
                Paragraph("<b>Issuing Authority:</b> Ministry of Education & Tech Guild &bull; <b>Verification ID:</b> NHIC-2026-9921", body_style),
            ]
            doc.build(story)

        # 2. Sample Image Certificate (PNG)
        img_path = os.path.join(upload_dir, 'sample_certificate_badge.png')
        if not os.path.exists(img_path):
            img = Image.new('RGB', (800, 560), color=(245, 247, 250))
            draw = ImageDraw.Draw(img)
            # Draw decorative border
            draw.rectangle([20, 20, 780, 540], outline=(30, 58, 138), width=6)
            draw.rectangle([28, 28, 772, 532], outline=(2, 132, 199), width=2)
            # Text
            draw.text((220, 80), "CERTIFICATE OF ACHIEVEMENT", fill=(30, 58, 138))
            draw.text((260, 140), "Presented for Distinguished Merit", fill=(71, 85, 105))
            draw.text((210, 220), "ACADEMIC & CO-CURRICULAR HONORS", fill=(2, 132, 199))
            draw.text((160, 300), "Demonstrated superior capability and verified completion.", fill=(51, 65, 85))
            draw.text((100, 440), "Official College Verification System", fill=(100, 116, 139))
            draw.text((540, 440), "Status: Digitally Authenticated", fill=(22, 163, 74))
            img.save(img_path)
    except Exception as e:
        print(f"Sample proof creation notice: {e}")

def seed_database(app):
    with app.app_context():
        db.create_all()

        upload_dir = app.config.get('UPLOAD_FOLDER') or os.path.join(app.root_path, 'static', 'uploads')
        create_sample_files(upload_dir)

        # 1. Seed Categories if empty
        if Category.query.count() == 0:
            categories = [
                Category(name="Technical & Hackathons", description="Coding competitions, hackathons, and software demos", points_weight=25, icon="bi-laptop"),
                Category(name="Research Papers & Publications", description="Peer-reviewed publications, conference papers, patents", points_weight=30, icon="bi-journal-code"),
                Category(name="Internships & Work Experience", description="Industry internships, technical trainee roles, freelance projects", points_weight=20, icon="bi-briefcase"),
                Category(name="Sports & Athletics", description="Inter-college tournaments, state/national sports achievements", points_weight=15, icon="bi-trophy"),
                Category(name="Cultural & Creative Arts", description="Debates, music, drama, fine arts, college festival leadership", points_weight=10, icon="bi-palette"),
                Category(name="Certifications & Online Courses", description="AWS, GCP, Coursera, NPTEL, Cisco, or industry certifications", points_weight=10, icon="bi-patch-check"),
            ]
            db.session.add_all(categories)
            db.session.commit()
            print("Categories seeded successfully.")

        # 2. Seed Admin & Faculty if not existing
        admin = User.query.filter_by(email="admin@college.edu").first()
        if not admin:
            admin = User(
                name="Dr. Arun Kumar",
                email="admin@college.edu",
                role="admin",
                department="Academic Affairs / Dean Office",
                student_id_no="ADMIN-001",
                bio="Dean of Student Affairs and Head of Institutional Accreditation."
            )
            admin.set_password("Admin@123")
            db.session.add(admin)

        faculty = User.query.filter_by(email="faculty.cs@college.edu").first()
        if not faculty:
            faculty = User(
                name="Prof. Arvind Kulkarni",
                email="faculty.cs@college.edu",
                role="faculty",
                department="Computer Science & Engineering",
                student_id_no="FAC-CS-104",
                bio="Associate Professor & Faculty Coordinator for Student Achievements."
            )
            faculty.set_password("Faculty@123")
            db.session.add(faculty)

        db.session.commit()

        # 3. Seed Students
        students_data = [
            {
                "name": "Aarav Sharma",
                "email": "aarav@student.edu",
                "department": "Computer Science & Engineering",
                "roll": "CS2023-010",
                "bio": "Passionate full-stack developer & competitive programmer. Interested in AI/ML and Cloud systems."
            },
            {
                "name": "Priya Patel",
                "email": "priya@student.edu",
                "department": "Information Technology",
                "roll": "IT2023-024",
                "bio": "Cybersecurity enthusiast, CTF player, and state badminton player."
            },
            {
                "name": "Rohan Verma",
                "email": "rohan@student.edu",
                "department": "Mechanical Engineering",
                "roll": "ME2023-055",
                "bio": "CAD designer, robotics team captain, and sports enthusiast."
            },
            {
                "name": "Ananya Iyer",
                "email": "ananya@student.edu",
                "department": "Electronics & Communication",
                "roll": "EC2023-018",
                "bio": "Embedded systems researcher, IoT hobbyist, and classical dancer."
            },
            {
                "name": "Vikram Singh",
                "email": "vikram@student.edu",
                "department": "Computer Science & Engineering",
                "roll": "CS2023-088",
                "bio": "Open-source contributor and machine learning enthusiast."
            }
        ]

        created_students = {}
        for s in students_data:
            existing = User.query.filter_by(email=s["email"]).first()
            if not existing:
                student = User(
                    name=s["name"],
                    email=s["email"],
                    role="student",
                    department=s["department"],
                    student_id_no=s["roll"],
                    bio=s["bio"]
                )
                student.set_password("Student@123")
                db.session.add(student)
                db.session.commit()
                created_students[s["email"]] = student
            else:
                created_students[s["email"]] = existing

        # 4. Seed Certificates
        cats = {c.name: c for c in Category.query.all()}
        
        certs_to_seed = [
            # Aarav
            {
                "student_email": "aarav@student.edu",
                "title": "1st Prize - Smart India Hackathon 2026",
                "cat": "Technical & Hackathons",
                "org": "Ministry of Education & AICTE",
                "date": date(2026, 3, 14),
                "cred_id": "SIH-2026-WIN-042",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Built an AI-driven disaster relief supply chain optimization platform.",
                "status": "Approved",
                "remarks": "Verified via SIH official result portal. Excellent work!",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "aarav@student.edu",
                "title": "Published Research Paper on Edge Computing in IEEE Xplore",
                "cat": "Research Papers & Publications",
                "org": "IEEE Computer Society",
                "date": date(2026, 1, 20),
                "cred_id": "10.1109/EDGEAI.2026.09182",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Co-authored research paper on low-latency inference on IoT edge clusters.",
                "status": "Approved",
                "remarks": "DOI verified and indexed.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "aarav@student.edu",
                "title": "AWS Certified Solutions Architect Associate",
                "cat": "Certifications & Online Courses",
                "org": "Amazon Web Services",
                "date": date(2025, 11, 10),
                "cred_id": "AWS-SAA-849102",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Demonstrated core cloud architectural design principles, VPC, and serverless architectures.",
                "status": "Approved",
                "remarks": "Credential verified on Credly.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "aarav@student.edu",
                "title": "Full-Stack Software Engineering Intern @ InnovateX Labs",
                "cat": "Internships & Work Experience",
                "org": "InnovateX Labs Pvt. Ltd.",
                "date": date(2026, 2, 28),
                "cred_id": "INX-INT-2026-88",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Worked on React, Flask APIs, and PostgreSQL microservices over 3 months.",
                "status": "Pending",
                "remarks": None,
                "verified_by": None,
                "verified_at": None
            },
            # Priya
            {
                "student_email": "priya@student.edu",
                "title": "National CTF Champion - CyberShield 2026",
                "cat": "Technical & Hackathons",
                "org": "National Cybersecurity Taskforce",
                "date": date(2026, 2, 18),
                "cred_id": "CS-CTF-2026-001",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Achieved Rank 1 nationally in binary exploitation, reverse engineering, and cryptography.",
                "status": "Approved",
                "remarks": "Verified against leaderboard standings.",
                "verified_by": admin.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "priya@student.edu",
                "title": "Data Science & Security Intern @ FinTech Corp",
                "cat": "Internships & Work Experience",
                "org": "FinTech Corp Global",
                "date": date(2026, 1, 15),
                "cred_id": "FT-2025-INTERN-49",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Developed fraud detection model using graph neural networks.",
                "status": "Approved",
                "remarks": "Letter of completion and HR verification confirmed.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "priya@student.edu",
                "title": "Gold Medalist - State Inter-University Badminton Championship",
                "cat": "Sports & Athletics",
                "org": "State University Sports Board",
                "date": date(2025, 12, 5),
                "cred_id": "SUSB-BADM-GM-01",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Won women's singles gold representing the university team.",
                "status": "Approved",
                "remarks": "Official university sports office stamp validated.",
                "verified_by": admin.id,
                "verified_at": datetime.now(timezone.utc)
            },
            # Rohan
            {
                "student_email": "rohan@student.edu",
                "title": "Lead Chassis Designer - Formula Student India 2026",
                "cat": "Technical & Hackathons",
                "org": "Formula Student India & SAE",
                "date": date(2026, 1, 28),
                "cred_id": "FSI-SAE-2026-CHAS",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Designed aerodynamic monocoque chassis that passed structural integrity benchmarks.",
                "status": "Approved",
                "remarks": "Validated by HOD Mechanical.",
                "verified_by": admin.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "rohan@student.edu",
                "title": "Robotics Simulation Intern @ MechaDynamics",
                "cat": "Internships & Work Experience",
                "org": "MechaDynamics Pvt. Ltd.",
                "date": date(2026, 3, 1),
                "cred_id": "MD-INT-9901",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Simulation modeling in ROS2 and Gazebo for robotic arms.",
                "status": "Pending",
                "remarks": None,
                "verified_by": None,
                "verified_at": None
            },
            {
                "student_email": "rohan@student.edu",
                "title": "Inter-College Photography Contest - Runner Up",
                "cat": "Cultural & Creative Arts",
                "org": "Arts Council Mumbai",
                "date": date(2025, 10, 12),
                "cred_id": "ACM-PHOTO-02",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Theme: Urban Architecture and Reflection.",
                "status": "Rejected",
                "remarks": "The submitted certificate does not bear the official signature and institutional seal. Please re-upload the verified copy.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            # Ananya
            {
                "student_email": "ananya@student.edu",
                "title": "1st Prize - National IoT Healthcare Innovation Challenge",
                "cat": "Technical & Hackathons",
                "org": "Biomedical Engineering Society",
                "date": date(2026, 2, 10),
                "cred_id": "BMES-IOT-099",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Developed wearable ECG and pulse-oximeter telemetry sensor node.",
                "status": "Approved",
                "remarks": "Patent application referenced in submission. Approved.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "ananya@student.edu",
                "title": "State Youth Festival Classical Dance Solo - 1st Position",
                "cat": "Cultural & Creative Arts",
                "org": "Department of Cultural Affairs",
                "date": date(2025, 11, 24),
                "cred_id": "DCA-DANCE-2025-01",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Performed Bharatanatyam Varnam in the open inter-university category.",
                "status": "Approved",
                "remarks": "State board certificate confirmed.",
                "verified_by": admin.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "ananya@student.edu",
                "title": "Microcontroller Firmware Intern @ EmbeddedSystems Inc",
                "cat": "Internships & Work Experience",
                "org": "EmbeddedSystems Solutions",
                "date": date(2026, 3, 5),
                "cred_id": "ESI-INT-2026",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "RTOS firmware programming on STM32 ARM Cortex-M4.",
                "status": "Pending",
                "remarks": None,
                "verified_by": None,
                "verified_at": None
            },
            # Vikram
            {
                "student_email": "vikram@student.edu",
                "title": "Core Contributor - Apache Software Foundation Incubator",
                "cat": "Technical & Hackathons",
                "org": "Apache Software Foundation",
                "date": date(2026, 1, 10),
                "cred_id": "ASF-COMM-VKR",
                "file_path": "sample_hackathon_award.pdf",
                "file_type": "pdf",
                "desc": "Authored 14 merged pull requests optimizing data pipeline connectors.",
                "status": "Approved",
                "remarks": "GitHub commit logs and PMC confirmation verified.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            },
            {
                "student_email": "vikram@student.edu",
                "title": "Deep Learning Specialization (5-Course Series)",
                "cat": "Certifications & Online Courses",
                "org": "DeepLearning.AI & Coursera",
                "date": date(2025, 12, 19),
                "cred_id": "COURSERA-DLS-9812",
                "file_path": "sample_certificate_badge.png",
                "file_type": "image",
                "desc": "Completed neural networks, CNNs, sequence models, and hyperparameter tuning.",
                "status": "Approved",
                "remarks": "Online credential link validated.",
                "verified_by": faculty.id,
                "verified_at": datetime.now(timezone.utc)
            }
        ]

        if Certificate.query.count() == 0:
            for c_data in certs_to_seed:
                student_user = created_students.get(c_data["student_email"])
                category_obj = cats.get(c_data["cat"])
                if student_user and category_obj:
                    cert = Certificate(
                        student_id=student_user.id,
                        category_id=category_obj.id,
                        title=c_data["title"],
                        issuing_org=c_data["org"],
                        issue_date=c_data["date"],
                        credential_id=c_data["cred_id"],
                        file_path=c_data["file_path"],
                        file_type=c_data["file_type"],
                        description=c_data["desc"],
                        status=c_data["status"],
                        admin_remarks=c_data["remarks"],
                        verified_by_id=c_data["verified_by"],
                        verified_at=c_data["verified_at"]
                    )
                    db.session.add(cert)
            db.session.commit()
            print("Sample certificates seeded successfully.")

        # 5. Seed some sample notifications
        if Notification.query.count() == 0:
            aarav = created_students.get("aarav@student.edu")
            if aarav:
                n1 = Notification(
                    user_id=aarav.id,
                    title="Certificate Approved! 🎉",
                    message="Your submission '1st Prize - Smart India Hackathon 2026' has been approved with 25 points.",
                    link="/dashboard",
                    is_read=True
                )
                n2 = Notification(
                    user_id=aarav.id,
                    title="Submission Under Review",
                    message="Your internship certificate '@ InnovateX Labs' is currently pending faculty verification.",
                    link="/dashboard",
                    is_read=False
                )
                db.session.add_all([n1, n2])
            db.session.commit()
            print("Notifications seeded successfully.")

if __name__ == '__main__':
    from app import app
    seed_database(app)
    print("Database seeding completed.")
