from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'admin', 'customer', or 'professional'
    status = db.Column(db.String(80), default='pending')
    blocked = db.Column(db.Boolean, default=False)

    # Relationships
    service_professionals = db.relationship('ServiceProfessional', backref='user', lazy=True)
    admin_actions = db.relationship('AdminAction', backref='admin_user', lazy=True)
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True)

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float(), nullable=False)
    time_required = db.Column(db.Integer)  # Time is in minutes
    created_at = db.Column(db.DateTime, default=func.now())

    # Relationships
    service_professionals = db.relationship('ServiceProfessional', backref='service', lazy=True)
    service_requests = db.relationship('ServiceRequest', backref='service', lazy=True)

class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    experience = db.Column(db.Text)
    verified = db.Column(db.Boolean(), nullable=False)  # Indicates if the professional is verified
    reviews = db.Column(db.Text)  # Consider a separate `Review` model for details
    verified = db.Column(db.Boolean, default=False)

    # Relationships
    service_requests = db.relationship('ServiceRequest', backref='professional', lazy=True)

class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    date_of_request = db.Column(db.DateTime, default=func.now())
    date_of_completion = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='requested')  
    remarks = db.Column(db.Text)

class AdminAction(db.Model):
    __tablename__ = 'admin_actions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Link to User as admin
    action = db.Column(db.Text, nullable=False)  # Description of the action (e.g., approval)
    description = db.Column(db.Text)
    action_date = db.Column(db.DateTime, default=func.now())
