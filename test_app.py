import os
import io
import unittest
from datetime import date
from app import app
from models import db, User, Category, Certificate, Notification
from pdf_generator import generate_portfolio_pdf

class CelestialAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_public_pages(self):
        """Test landing page, showcase wall, and leaderboard."""
        r1 = self.client.get('/')
        self.assertEqual(r1.status_code, 200)
        self.assertIn(b'Celestial', r1.data)
        self.assertIn(b'Showcase', r1.data)

        r2 = self.client.get('/showcase')
        self.assertEqual(r2.status_code, 200)
        self.assertIn(b'Campus Achievement Showcase', r2.data)

        r3 = self.client.get('/leaderboard')
        self.assertEqual(r3.status_code, 200)
        self.assertIn(b'Campus Achievement Leaderboard', r3.data)

    def test_student_portfolio_and_pdf(self):
        """Test public student portfolio and PDF download."""
        with app.app_context():
            student = User.query.filter_by(role='student').first()
            self.assertIsNotNone(student)
            student_id = student.id

        # Public portfolio page
        r = self.client.get(f'/portfolio/{student_id}')
        self.assertEqual(r.status_code, 200)

        # PDF generation test
        r_pdf = self.client.get(f'/portfolio/{student_id}/download-pdf')
        self.assertEqual(r_pdf.status_code, 200)
        self.assertEqual(r_pdf.mimetype, 'application/pdf')
        self.assertGreater(len(r_pdf.data), 1000)

    def test_login_and_student_flow(self):
        """Test student login and dashboard."""
        # 1. Login
        login_res = self.client.post('/login', data={
            'email': 'aarav@student.edu',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Welcome back', login_res.data)

        # 2. Student Dashboard
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'My Achievement Portfolio Record', dash_res.data)

        # 3. Submit New Certificate
        with app.app_context():
            cat = Category.query.first()
            cat_id = cat.id

        fake_pdf = (io.BytesIO(b'%PDF-1.4 test certificate file'), 'test_hackathon.pdf')
        upload_res = self.client.post('/certificate/upload', data={
            'title': 'Test Hackathon Win 2026',
            'category_id': cat_id,
            'issuing_org': 'Hackathon Council',
            'issue_date': '2026-03-01',
            'credential_id': 'TEST-999',
            'description': 'Automated test submission',
            'file': fake_pdf
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(upload_res.status_code, 200)
        self.assertIn(b'Certificate submitted successfully', upload_res.data)

    def test_faculty_verification_flow(self):
        """Test faculty login, pending queue, and approval workflow."""
        # 1. Login as faculty
        login_res = self.client.post('/login', data={
            'email': 'faculty.cs@college.edu',
            'password': 'Faculty@123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

        # 2. Admin Dashboard
        admin_res = self.client.get('/admin/dashboard')
        self.assertEqual(admin_res.status_code, 200)
        self.assertIn(b'Verification & Review Queue', admin_res.data)

        # 3. Find a pending certificate and approve it
        with app.app_context():
            pending_cert = Certificate.query.filter_by(status='Pending').first()
            if pending_cert:
                cert_id = pending_cert.id
                verify_res = self.client.post(f'/admin/verify/{cert_id}', data={
                    'action': 'approve',
                    'remarks': 'Approved in automated test suite.'
                }, follow_redirects=True)
                self.assertEqual(verify_res.status_code, 200)

                updated = db.session.get(Certificate, cert_id)
                self.assertEqual(updated.status, 'Approved')
                self.assertEqual(updated.admin_remarks, 'Approved in automated test suite.')

    def test_analytics_api(self):
        """Test the analytics JSON data endpoint."""
        # Login first as faculty
        self.client.post('/login', data={
            'email': 'admin@college.edu',
            'password': 'Admin@123'
        })
        res = self.client.get('/api/analytics-data')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('departments', data)
        self.assertIn('categories', data)
        self.assertIn('status', data)

    def test_account_switching_flow(self):
        """Test that submitting a login for a different user cleanly switches accounts."""
        # 1. Log in as Aarav
        r1 = self.client.post('/login', data={
            'email': 'aarav@student.edu',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertEqual(r1.status_code, 200)
        dash1 = self.client.get('/dashboard')
        self.assertIn(b'Aarav Sharma', dash1.data)

        # 2. Directly log in as Priya WITHOUT explicit logout
        r2 = self.client.post('/login', data={
            'email': 'priya@student.edu',
            'password': 'Student@123'
        }, follow_redirects=True)
        self.assertEqual(r2.status_code, 200)
        dash2 = self.client.get('/dashboard')
        self.assertIn(b'Priya Patel', dash2.data)
        self.assertNotIn(b'Aarav Sharma', dash2.data)

    def test_database_file_fallback_delivery(self):
        """Test that uploaded files stored in DB can be served even if deleted from disk."""
        # 1. Login as student
        self.client.post('/login', data={
            'email': 'aarav@student.edu',
            'password': 'Student@123'
        })

        with app.app_context():
            cat = Category.query.first()
            cat_id = cat.id

        unique_content = b'%PDF-1.4 persistent-db-test-content-unique'
        fake_pdf = (io.BytesIO(unique_content), 'cold_start_test.pdf')
        upload_res = self.client.post('/certificate/upload', data={
            'title': 'Cold Start Resilient Cert',
            'category_id': cat_id,
            'issuing_org': 'Resilience Org',
            'issue_date': '2026-03-10',
            'description': 'Testing DB BLOB fallback',
            'file': fake_pdf
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(upload_res.status_code, 200)

        # Find the newly created certificate's filename
        with app.app_context():
            cert = Certificate.query.filter_by(title='Cold Start Resilient Cert').first()
            self.assertIsNotNone(cert)
            self.assertIsNotNone(cert.file_data)
            filename = cert.file_path
            disk_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 2. Simulate cold-start / serverless worker isolation by deleting disk file
        if os.path.exists(disk_path):
            os.remove(disk_path)
        self.assertFalse(os.path.exists(disk_path))

        # 3. Request the file through the server - should recover from DB!
        file_res = self.client.get(f'/static/uploads/{filename}')
        self.assertEqual(file_res.status_code, 200)
        self.assertEqual(file_res.data, unique_content)

    def test_cache_control_headers(self):
        """Test that authenticated pages have no-cache headers to prevent cross-account display leakage."""
        self.client.post('/login', data={
            'email': 'aarav@student.edu',
            'password': 'Student@123'
        })
        dash = self.client.get('/dashboard')
        self.assertEqual(dash.status_code, 200)
        self.assertIn('no-store', dash.headers.get('Cache-Control', ''))

if __name__ == '__main__':
    unittest.main()

