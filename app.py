import os
import uuid
from datetime import datetime, date, timezone
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    jsonify, send_file, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc

from models import db, User, Category, Certificate, Notification
from pdf_generator import generate_portfolio_pdf

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'celestial-super-secret-key-2026-hackathon')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

DEPARTMENTS = [
    'Computer Science & Engineering',
    'Information Technology',
    'Electronics & Communication',
    'Mechanical Engineering',
    'Civil Engineering',
    'Electrical Engineering',
    'Chemical Engineering',
    'Management Studies & MBA'
]

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Role-based access decorators
def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            flash('Access restricted to students only.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_faculty:
            flash('Access restricted to faculty or admin personnel.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Context Processors
@app.context_processor
def inject_global_vars():
    unread_count = 0
    recent_notifications = []
    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        recent_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()
    
    categories = Category.query.all() if Category.query.count() > 0 else []
    return dict(
        unread_count=unread_count,
        recent_notifications=recent_notifications,
        global_categories=categories,
        all_departments=DEPARTMENTS,
        now=datetime.now(timezone.utc)
    )


# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def index():
    # Overall statistics
    total_approved = Certificate.query.filter_by(status='Approved').count()
    total_students = User.query.filter_by(role='student').count()
    total_pending = Certificate.query.filter_by(status='Pending').count()
    total_categories = Category.query.count()

    # Recent 6 approved achievements for showcase snippet
    recent_achievements = Certificate.query.filter_by(status='Approved')\
        .order_by(Certificate.issue_date.desc()).limit(6).all()

    # Top 3 leaderboard leaders for the home spotlight
    students = User.query.filter_by(role='student').all()
    # Sort by total points descending
    ranked_students = sorted(students, key=lambda s: s.total_points, reverse=True)[:3]

    return render_template(
        'index.html',
        total_approved=total_approved,
        total_students=total_students,
        total_pending=total_pending,
        total_categories=total_categories,
        recent_achievements=recent_achievements,
        top_students=ranked_students
    )


@app.route('/showcase')
def showcase():
    category_id = request.args.get('category', type=int)
    department = request.args.get('department', type=str)
    search_query = request.args.get('q', type=str, default='').strip()
    year = request.args.get('year', type=int)

    query = Certificate.query.join(User, Certificate.student_id == User.id)\
        .filter(Certificate.status == 'Approved')

    if category_id:
        query = query.filter(Certificate.category_id == category_id)
    if department:
        query = query.filter(User.department == department)
    if year:
        query = query.filter(func.strftime('%Y', Certificate.issue_date) == str(year))
    if search_query:
        query = query.filter(
            (Certificate.title.ilike(f'%{search_query}%')) |
            (Certificate.issuing_org.ilike(f'%{search_query}%')) |
            (User.name.ilike(f'%{search_query}%'))
        )

    certificates = query.order_by(Certificate.issue_date.desc()).all()
    
    # Available years for filter dropdown
    all_approved = Certificate.query.filter_by(status='Approved').all()
    years = sorted(list({c.issue_date.year for c in all_approved if c.issue_date}), reverse=True)

    return render_template(
        'showcase.html',
        certificates=certificates,
        selected_category=category_id,
        selected_department=department,
        selected_year=year,
        search_query=search_query,
        years=years
    )


@app.route('/leaderboard')
def leaderboard():
    department = request.args.get('department', type=str)
    
    students_query = User.query.filter_by(role='student')
    if department:
        students_query = students_query.filter_by(department=department)

    students = students_query.all()
    
    # Calculate ranking list with points and approved certificates count
    leaderboard_data = []
    for s in students:
        total_pts = s.total_points
        approved_count = len(s.approved_certificates)
        leaderboard_data.append({
            'user': s,
            'points': total_pts,
            'approved_count': approved_count
        })

    # Sort primarily by points (descending), secondarily by approved certificate count
    leaderboard_data.sort(key=lambda x: (x['points'], x['approved_count']), reverse=True)

    # Assign rank with handling for podium
    top_three = leaderboard_data[:3]
    rest_rankings = leaderboard_data[3:]

    return render_template(
        'leaderboard.html',
        top_three=top_three,
        rankings=leaderboard_data,
        rest_rankings=rest_rankings,
        selected_department=department
    )


@app.route('/portfolio/<int:student_id>')
def public_portfolio(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        abort(404)
    
    approved_certs = Certificate.query.filter_by(student_id=student.id, status='Approved')\
        .order_by(Certificate.issue_date.desc()).all()

    return render_template(
        'public_portfolio.html',
        student=student,
        approved_certs=approved_certs
    )


@app.route('/portfolio/<int:student_id>/download-pdf')
def download_student_portfolio_pdf(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        abort(404)

    pdf_buffer = generate_portfolio_pdf(student)
    safe_name = "".join(c for c in student.name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"{safe_name.replace(' ', '_')}_Verified_Portfolio.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student_dashboard' if current_user.is_student else 'admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        department = request.form.get('department', '').strip()
        student_id_no = request.form.get('student_id_no', '').strip()
        bio = request.form.get('bio', '').strip()

        if not name or not email or not password or not department:
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role, department=department)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role, department=department)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role, department=department)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Security check: only allow 'student' or 'faculty' signup directly
        if role not in ['student', 'faculty']:
            role = 'student'

        new_user = User(
            name=name,
            email=email,
            role=role,
            department=department,
            student_id_no=student_id_no if role == 'student' else f"FAC-{uuid.uuid4().hex[:4].upper()}",
            bio=bio
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f'Account created successfully as {role.capitalize()}! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_student:
            return redirect(url_for('student_dashboard'))
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.name}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        
        if user.is_student:
            return redirect(url_for('student_dashboard'))
        return redirect(url_for('admin_dashboard'))

    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        student_id_no = request.form.get('student_id_no', '').strip()
        bio = request.form.get('bio', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if not name or not department:
            flash('Name and Department cannot be empty.', 'danger')
            return redirect(url_for('profile'))

        current_user.name = name
        current_user.department = department
        current_user.bio = bio
        if current_user.is_student:
            current_user.student_id_no = student_id_no

        if new_password:
            if not current_password or not current_user.check_password(current_password):
                flash('Current password is incorrect. Profile details saved without password change.', 'warning')
            else:
                current_user.set_password(new_password)
                flash('Password updated successfully!', 'success')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


# ==========================================
# STUDENT PORTAL ROUTES
# ==========================================

@app.route('/dashboard')
@login_required
@student_required
def student_dashboard():
    # Fetch all certificates belonging to the student
    certificates = Certificate.query.filter_by(student_id=current_user.id)\
        .order_by(Certificate.created_at.desc()).all()

    total_submissions = len(certificates)
    approved_count = sum(1 for c in certificates if c.status == 'Approved')
    pending_count = sum(1 for c in certificates if c.status == 'Pending')
    rejected_count = sum(1 for c in certificates if c.status == 'Rejected')
    total_points = current_user.total_points

    return render_template(
        'student/dashboard.html',
        certificates=certificates,
        total_submissions=total_submissions,
        approved_count=approved_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        total_points=total_points
    )


@app.route('/certificate/upload', methods=['GET', 'POST'])
@login_required
@student_required
def upload_certificate():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        issuing_org = request.form.get('issuing_org', '').strip()
        issue_date_str = request.form.get('issue_date', '').strip()
        credential_id = request.form.get('credential_id', '').strip()
        credential_url = request.form.get('credential_url', '').strip()
        description = request.form.get('description', '').strip()
        file = request.files.get('file')

        if not title or not category_id or not issuing_org or not issue_date_str or not file:
            flash('Please provide all required fields including the certificate document.', 'danger')
            return redirect(url_for('upload_certificate'))

        if file.filename == '' or not allowed_file(file.filename):
            flash('Invalid file format. Please upload a PDF or image (PNG, JPG, JPEG, WEBP).', 'danger')
            return redirect(url_for('upload_certificate'))

        try:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid issue date format.', 'danger')
            return redirect(url_for('upload_certificate'))

        # Secure file saving
        ext = file.filename.rsplit('.', 1)[1].lower()
        file_type = 'pdf' if ext == 'pdf' else 'image'
        safe_base = secure_filename(file.filename.rsplit('.', 1)[0])[:30]
        unique_filename = f"{uuid.uuid4().hex[:10]}_{safe_base}.{ext}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(save_path)

        new_cert = Certificate(
            student_id=current_user.id,
            category_id=category_id,
            title=title,
            issuing_org=issuing_org,
            issue_date=issue_date,
            credential_id=credential_id,
            credential_url=credential_url,
            file_path=unique_filename,
            file_type=file_type,
            description=description,
            status='Pending'
        )
        db.session.add(new_cert)
        db.session.commit()

        flash('Certificate submitted successfully! It is now in the faculty verification queue.', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('student/upload.html')


@app.route('/certificate/<int:cert_id>/edit', methods=['GET', 'POST'])
@login_required
@student_required
def edit_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)

    # Security check: must belong to current student
    if cert.student_id != current_user.id:
        abort(403)

    # Can only edit if status is Pending (or if Rejected and re-submitting)
    if cert.status == 'Approved':
        flash('Approved certificates cannot be modified.', 'warning')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        issuing_org = request.form.get('issuing_org', '').strip()
        issue_date_str = request.form.get('issue_date', '').strip()
        credential_id = request.form.get('credential_id', '').strip()
        credential_url = request.form.get('credential_url', '').strip()
        description = request.form.get('description', '').strip()
        file = request.files.get('file')

        if not title or not category_id or not issuing_org or not issue_date_str:
            flash('Please fill in all required fields.', 'danger')
            return render_template('student/edit.html', cert=cert)

        try:
            issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid issue date format.', 'danger')
            return render_template('student/edit.html', cert=cert)

        # Update details
        cert.title = title
        cert.category_id = category_id
        cert.issuing_org = issuing_org
        cert.issue_date = issue_date
        cert.credential_id = credential_id
        cert.credential_url = credential_url
        cert.description = description
        
        # If was rejected, resetting to Pending on edit
        if cert.status == 'Rejected':
            cert.status = 'Pending'
            cert.admin_remarks = f"Re-submitted by student on {datetime.now(timezone.utc).strftime('%b %d, %Y')}"

        # If a new file is uploaded
        if file and file.filename != '':
            if not allowed_file(file.filename):
                flash('Invalid file format. Please upload PDF or image.', 'danger')
                return render_template('student/edit.html', cert=cert)

            ext = file.filename.rsplit('.', 1)[1].lower()
            file_type = 'pdf' if ext == 'pdf' else 'image'
            safe_base = secure_filename(file.filename.rsplit('.', 1)[0])[:30]
            unique_filename = f"{uuid.uuid4().hex[:10]}_{safe_base}.{ext}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(save_path)

            cert.file_path = unique_filename
            cert.file_type = file_type

        db.session.commit()
        flash('Certificate updated successfully and resubmitted for verification!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('student/edit.html', cert=cert)


@app.route('/certificate/<int:cert_id>/delete', methods=['POST'])
@login_required
@student_required
def delete_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)

    if cert.student_id != current_user.id:
        abort(403)

    if cert.status == 'Approved':
        flash('Approved certificates cannot be deleted directly.', 'warning')
        return redirect(url_for('student_dashboard'))

    db.session.delete(cert)
    db.session.commit()
    flash('Certificate submission deleted.', 'info')
    return redirect(url_for('student_dashboard'))


# ==========================================
# FACULTY / ADMIN PORTAL ROUTES
# ==========================================

@app.route('/admin/dashboard')
@login_required
@faculty_required
def admin_dashboard():
    # Filter params
    category_id = request.args.get('category', type=int)
    department = request.args.get('department', type=str)
    search_query = request.args.get('q', type=str, default='').strip()

    # Query for pending submissions
    query = Certificate.query.join(User, Certificate.student_id == User.id)\
        .filter(Certificate.status == 'Pending')

    if category_id:
        query = query.filter(Certificate.category_id == category_id)
    if department:
        query = query.filter(User.department == department)
    if search_query:
        query = query.filter(
            (Certificate.title.ilike(f'%{search_query}%')) |
            (Certificate.issuing_org.ilike(f'%{search_query}%')) |
            (User.name.ilike(f'%{search_query}%')) |
            (User.student_id_no.ilike(f'%{search_query}%'))
        )

    pending_submissions = query.order_by(Certificate.created_at.asc()).all()

    # Metrics
    total_pending = Certificate.query.filter_by(status='Pending').count()
    total_approved = Certificate.query.filter_by(status='Approved').count()
    total_rejected = Certificate.query.filter_by(status='Rejected').count()
    total_students = User.query.filter_by(role='student').count()

    return render_template(
        'admin/dashboard.html',
        pending_submissions=pending_submissions,
        total_pending=total_pending,
        total_approved=total_approved,
        total_rejected=total_rejected,
        total_students=total_students,
        selected_category=category_id,
        selected_department=department,
        search_query=search_query
    )


@app.route('/admin/verify/<int:cert_id>', methods=['POST'])
@login_required
@faculty_required
def verify_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    action = request.form.get('action')  # 'approve' or 'reject'
    remarks = request.form.get('remarks', '').strip()

    if action not in ['approve', 'reject']:
        flash('Invalid action requested.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if action == 'approve':
        cert.status = 'Approved'
        cert.admin_remarks = remarks or 'Verified and approved by faculty.'
        cert.verified_by_id = current_user.id
        cert.verified_at = datetime.now(timezone.utc)

        # Send notification to student
        pts = cert.category.points_weight if cert.category else 10
        notif = Notification(
            user_id=cert.student_id,
            title="Certificate Approved! 🏆",
            message=f"Your achievement '{cert.title}' was approved (+{pts} pts) by {current_user.name}.",
            link="/dashboard"
        )
        db.session.add(notif)
        flash(f"Certificate '{cert.title}' was approved successfully (+{pts} points awarded).", 'success')

    elif action == 'reject':
        cert.status = 'Rejected'
        cert.admin_remarks = remarks or 'Certificate could not be verified. Please check requirements and re-submit.'
        cert.verified_by_id = current_user.id
        cert.verified_at = datetime.now(timezone.utc)

        # Send notification to student
        notif = Notification(
            user_id=cert.student_id,
            title="Certificate Verification Update ⚠️",
            message=f"Your achievement '{cert.title}' was rejected. Remarks: {cert.admin_remarks}",
            link="/dashboard"
        )
        db.session.add(notif)
        flash(f"Certificate '{cert.title}' has been marked as rejected with remarks.", 'warning')

    db.session.commit()
    return redirect(request.referrer or url_for('admin_dashboard'))


@app.route('/admin/all-submissions')
@login_required
@faculty_required
def all_submissions():
    status = request.args.get('status', type=str)
    category_id = request.args.get('category', type=int)
    department = request.args.get('department', type=str)
    search_query = request.args.get('q', type=str, default='').strip()

    query = Certificate.query.join(User, Certificate.student_id == User.id)

    if status and status in ['Approved', 'Pending', 'Rejected']:
        query = query.filter(Certificate.status == status)
    if category_id:
        query = query.filter(Certificate.category_id == category_id)
    if department:
        query = query.filter(User.department == department)
    if search_query:
        query = query.filter(
            (Certificate.title.ilike(f'%{search_query}%')) |
            (Certificate.issuing_org.ilike(f'%{search_query}%')) |
            (User.name.ilike(f'%{search_query}%'))
        )

    submissions = query.order_by(Certificate.created_at.desc()).all()

    return render_template(
        'admin/all_submissions.html',
        submissions=submissions,
        selected_status=status,
        selected_category=category_id,
        selected_department=department,
        search_query=search_query
    )


@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@faculty_required
def manage_categories():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            points_weight = request.form.get('points_weight', type=int, default=10)
            icon = request.form.get('icon', 'bi-award').strip()

            if not name or points_weight is None:
                flash('Category name and points weight are required.', 'danger')
            else:
                existing = Category.query.filter(func.lower(Category.name) == name.lower()).first()
                if existing:
                    flash('A category with this name already exists.', 'warning')
                else:
                    new_cat = Category(name=name, description=description, points_weight=points_weight, icon=icon)
                    db.session.add(new_cat)
                    db.session.commit()
                    flash(f'Category "{name}" added successfully with weight {points_weight} pts!', 'success')

        elif action == 'update':
            cat_id = request.form.get('category_id', type=int)
            points_weight = request.form.get('points_weight', type=int)
            description = request.form.get('description', '').strip()
            icon = request.form.get('icon', 'bi-award').strip()

            cat = db.session.get(Category, cat_id)
            if cat and points_weight is not None:
                cat.points_weight = points_weight
                cat.description = description
                cat.icon = icon
                db.session.commit()
                flash(f'Category "{cat.name}" updated successfully.', 'success')

        return redirect(url_for('manage_categories'))

    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)


@app.route('/admin/analytics')
@login_required
@faculty_required
def analytics():
    return render_template('admin/analytics.html')


@app.route('/api/analytics-data')
@login_required
@faculty_required
def api_analytics_data():
    # 1. Department-wise achievement count (Approved only)
    dept_counts = db.session.query(
        User.department, func.count(Certificate.id)
    ).join(Certificate, User.id == Certificate.student_id)\
     .filter(Certificate.status == 'Approved')\
     .group_by(User.department).all()

    dept_labels = [d[0] for d in dept_counts] or ["No Data"]
    dept_values = [d[1] for d in dept_counts] or [0]

    # 2. Category breakdown (Approved)
    cat_counts = db.session.query(
        Category.name, func.count(Certificate.id)
    ).join(Certificate, Category.id == Certificate.category_id)\
     .filter(Certificate.status == 'Approved')\
     .group_by(Category.name).all()

    cat_labels = [c[0] for c in cat_counts] or ["No Data"]
    cat_values = [c[1] for c in cat_counts] or [0]

    # 3. Status Breakdown
    status_counts = db.session.query(
        Certificate.status, func.count(Certificate.id)
    ).group_by(Certificate.status).all()

    status_dict = {s[0]: s[1] for s in status_counts}
    status_labels = ['Approved', 'Pending', 'Rejected']
    status_values = [status_dict.get('Approved', 0), status_dict.get('Pending', 0), status_dict.get('Rejected', 0)]

    return jsonify({
        'departments': {'labels': dept_labels, 'data': dept_values},
        'categories': {'labels': cat_labels, 'data': cat_values},
        'status': {'labels': status_labels, 'data': status_values}
    })


# ==========================================
# NOTIFICATIONS API
# ==========================================

@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
