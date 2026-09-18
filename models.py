from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'faculty', 'admin'
    department = db.Column(db.String(100), nullable=False)  # e.g., 'Computer Science & Engineering'
    student_id_no = db.Column(db.String(50), nullable=True)  # e.g., 'CS-2023-042'
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Relationships
    certificates = db.relationship('Certificate', backref='student', lazy=True, foreign_keys='Certificate.student_id', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_faculty(self):
        return self.role in ['faculty', 'admin']

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def total_points(self):
        """Calculate total points from approved certificates based on category points weight."""
        points = 0
        for cert in self.certificates:
            if cert.status == 'Approved' and cert.category:
                points += cert.category.points_weight
        return points

    @property
    def approved_certificates(self):
        return [cert for cert in self.certificates if cert.status == 'Approved']

    @property
    def pending_certificates(self):
        return [cert for cert in self.certificates if cert.status == 'Pending']

    @property
    def rejected_certificates(self):
        return [cert for cert in self.certificates if cert.status == 'Rejected']

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    points_weight = db.Column(db.Integer, nullable=False, default=10)
    icon = db.Column(db.String(50), default='bi-award')  # Bootstrap icon class

    certificates = db.relationship('Certificate', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name} ({self.points_weight} pts)>'


class Certificate(db.Model):
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    issuing_org = db.Column(db.String(150), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    credential_id = db.Column(db.String(100), nullable=True)
    credential_url = db.Column(db.String(255), nullable=True)
    
    file_path = db.Column(db.String(255), nullable=False)  # filename inside static/uploads/
    file_type = db.Column(db.String(10), nullable=False)    # 'pdf', 'image'
    description = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), nullable=False, default='Pending')  # 'Pending', 'Approved', 'Rejected'
    admin_remarks = db.Column(db.Text, nullable=True)
    
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_by = db.relationship('User', foreign_keys=[verified_by_id])
    verified_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    @property
    def points(self):
        if self.status == 'Approved' and self.category:
            return self.category.points_weight
        return 0

    def __repr__(self):
        return f'<Certificate #{self.id} {self.title} - {self.status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f'<Notification #{self.id} for User {self.user_id}>'
