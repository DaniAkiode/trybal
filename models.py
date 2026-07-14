from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    progress = db.relationship('UserProgress', backref = 'user', lazy=True)
    streak = db.relationship('UserStreak', backref='user', lazy=True, uselist=False)

    def set_password(self, password):
        """Hash and store the password — never store plain text."""
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        """Check a plain text password against the stored hash"""
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.email}>'
    

class UserProgress(db.Model):
    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, nullable=False)
    language_code = db.Column(db.String(20), nullable=False, default='yoruba')
    completed =db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProgress user={self.user_id} lesson={self.lesson_id}>'

class UserStreak(db.Model):
    __tablename__ = 'user_streaks'

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_streak  = db.Column(db.Integer, default=0)
    longest_streak  = db.Column(db.Integer, default=0)
    last_active     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserStreak user={self.user_id} streak={self.current_streak}>'