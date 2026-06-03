from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserProgress, UserStreak
from datetime import datetime

auth = Blueprint('auth', __name__)

# ── registration ─────────────────────────────────────────

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        print("DEBUG: User already authenticated, redirecting home")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        errors = []

        if not username or len(username) < 2:
            errors.append('Username must be at least 2 characters.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if User.query.filter_by(email=email).first():
            errors.append('An account with that email already exists.')
        if User.query.filter_by(username=username).first():
            errors.append('That username is already taken.')

        if errors:
            return render_template('register.html', errors=errors,
                                   username=username, email=email)

        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            streak = UserStreak(user_id=user.id)
            db.session.add(streak)
            db.session.commit()

            login_user(user)

            return redirect(url_for('auth.migrate_progress_page'))

        except Exception as e:
            db.session.rollback()
            return render_template('register.html', 
                                   errors=[str(e)],
                                   username=username, 
                                   email=email)

    return render_template('register.html', errors=[], username='', email='')

@auth.route('/welcome')
@login_required
def migrate_progress_page():
    return render_template('welcome.html')


# -- Login --------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return render_template('login.html', error='Invalid email or password', email=email)

        login_user(user)
        return redirect(url_for('index'))
    return render_template('login.html', error=None, email='')


# ---logout-------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --progress migration ----

@auth.route('/api/migrate-progress', methods=['POST'])
@login_required
def migrate_progress():
    data = request.get_json()
    completed_lessons = data.get('completedLessons', [])
    scores = data.get('scores', {})

    for lesson_id in completed_lessons:
        # Check if progress already exists for this lesson
        existing = UserProgress.query.filter_by( 
            user_id=current_user.id,
            lesson_id=lesson_id
        ).first()

        if not existing:
            score_data = scores.get(str(lesson_id), {})
            progress = UserProgress(
                user_id = current_user.id,
                lesson_id = lesson_id,
                completed = True,
                score = score_data.get('score', 0),
                total = score_data.get('total', 0),
                completed_at = datetime.utcnow()
            )
            db.session.add(progress)
    db.session.commit()
    return jsonify({'status': 'ok', 'migrated': len(completed_lessons)})


