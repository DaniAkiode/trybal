from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from datetime import datetime
from extensions import csrf, limiter
import json
import os
import random


load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///trybal.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 #16KB max request size

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

csrf.init_app(app)

csrf.init_app(app)

# Manually register csrf_token as a template global
@app.context_processor
def csrf_context():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

limiter.init_app(app)

from models import db, User, UserProgress, UserStreak
db.init_app(app)

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.after_request
def set_security_headers(response):
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Force HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Control what resources can be loaded
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    return response


from flask_limiter.errors import RateLimitExceeded

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    return render_template('rate_limited.html'), 429

with app.app_context():
    db.create_all()

def load_json(filename):
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_language(code):
    languages = load_json('languages.json')['languages']
    for lang in languages:
        if lang['code'] == code:
            return lang
    return None

# ── home — language selection ────────────────────────
@app.route('/')
def index():
    languages = load_json('languages.json')['languages']
    return render_template('index.html', languages=languages)

# ── language home — lessons for a language ───────────
@app.route('/<language_code>')
def language_home(language_code):
    lang = get_language(language_code)
    if not lang:
        return "Language not found", 404
    if not lang['available']:
        return render_template('coming_soon.html', language=lang)

    lessons_data = load_json(lang['lessons_file'])
    return render_template('lessons.html',
                           language=lang,
                           lessons=lessons_data['lessons'])

# ── lesson ───────────────────────────────────────────
@app.route('/<language_code>/lesson/<int:lesson_id>')
def lesson(language_code, lesson_id):
    lang = get_language(language_code)
    if not lang or not lang['available']:
        return "Not found", 404

    all_words    = load_json(lang['words_file'])['words']
    lessons_data = load_json(lang['lessons_file'])['lessons']

    current_lesson = None
    for l in lessons_data:
        if l['id'] == lesson_id:
            current_lesson = l
            break

    if current_lesson is None:
        return "Lesson not found", 404

    word_ids     = current_lesson['word_ids']
    lesson_words = [w for w in all_words if w['id'] in word_ids]

    return render_template('lesson.html',
                           language=lang,
                           lesson=current_lesson,
                           words=lesson_words)

# ── quiz ─────────────────────────────────────────────
@app.route('/<language_code>/quiz/<int:lesson_id>')
def quiz(language_code, lesson_id):
    lang = get_language(language_code)
    if not lang or not lang['available']:
        return "Not found", 404

    all_words    = load_json(lang['words_file'])['words']
    lessons_data = load_json(lang['lessons_file'])['lessons']

    current_lesson = None
    for l in lessons_data:
        if l['id'] == lesson_id:
            current_lesson = l
            break

    if current_lesson is None:
        return "Lesson not found", 404

    word_ids     = current_lesson['word_ids']
    lesson_words = [w for w in all_words if w['id'] in word_ids]

    questions = []
    for word in lesson_words:
        other_words   = [w for w in all_words if w['id'] not in word_ids]
        distractors   = random.sample(other_words, min(3, len(other_words)))
        wrong_answers = [d['translation'] for d in distractors]
        choices       = wrong_answers + [word['translation']]
        random.shuffle(choices)

        questions.append({
            'word':          word['word'],
            'pronunciation': word['pronunciation'],
            'correct':       word['translation'],
            'cultural_note': word['cultural_note'],
            'choices':       choices
        })

    return render_template('quiz.html',
                           language=lang,
                           lesson=current_lesson,
                           questions=questions)

# ── API: my progress ─────────────────────────────────
@app.route('/api/my-progress')
@csrf.exempt
def my_progress():
    if current_user.is_authenticated:
        completed = UserProgress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).all()
        lesson_ids = [p.lesson_id for p in completed]
        return jsonify({'completedLessons': lesson_ids, 'source': 'database'})
    return jsonify({'completedLessons': [], 'source': 'guest'})

# ── API: complete lesson ──────────────────────────────
@app.route('/api/complete-lesson', methods=['POST'])
@csrf.exempt
def complete_lesson():
    if not current_user.is_authenticated:
        return jsonify({'status': 'guest'})

    data      = request.get_json()
    lesson_id = data.get('lesson_id')
    score     = data.get('score', 0)
    total     = data.get('total', 0)

    # ── save lesson progress ─────────────────────────
    existing = UserProgress.query.filter_by(
        user_id=current_user.id,
        lesson_id=lesson_id
    ).first()

    if existing:
        existing.score        = score
        existing.total        = total
        existing.completed    = True
        existing.completed_at = datetime.utcnow()
    else:
        progress = UserProgress(
            user_id      = current_user.id,
            lesson_id    = lesson_id,
            completed    = True,
            score        = score,
            total        = total,
            completed_at = datetime.utcnow()
        )
        db.session.add(progress)

    # ── update streak ────────────────────────────────
    streak = UserStreak.query.filter_by(user_id=current_user.id).first()

    if not streak:
        streak = UserStreak(user_id=current_user.id)
        db.session.add(streak)

    today     = datetime.utcnow().date()
    last_active = streak.last_active.date() if streak.last_active else None

    if last_active is None or streak.current_streak == 0:
        # First time completing anything
        streak.current_streak = 1
    elif last_active == today:
        # Already completed something today — don't double count
        pass
    elif (today - last_active).days == 1:
        # Completed yesterday — keep the streak going
        streak.current_streak += 1
    else:
        # Missed one or more days — reset
        streak.current_streak = 1

    # Update longest streak if current beats it
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    streak.last_active = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status':         'ok',
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak
    })

# ── API: words and lessons ────────────────────────────
@app.route('/api/<language_code>/words')
def get_words(language_code):
    lang = get_language(language_code)
    if not lang:
        return jsonify({'error': 'Language not found'}), 404
    words_data = load_json(lang['words_file'])
    return jsonify(words_data['words'])

@app.route('/api/<language_code>/lessons')
def get_lessons(language_code):
    lang = get_language(language_code)
    if not lang:
        return jsonify({'error': 'Language not found'}), 404
    lessons_data = load_json(lang['lessons_file'])
    return jsonify(lessons_data['lessons'])

# ── progress dashboard ────────────────────────────────
@app.route('/progress')
def progress():
    if not current_user.is_authenticated:
        return render_template('progress.html',
                               authenticated=False,
                               stats=None,
                               completed_lessons=None)

    user_progress = UserProgress.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(UserProgress.completed_at.desc()).all()

    lessons_data = load_json('yoruba_lessons.json')['lessons']
    lessons_map  = {l['id']: l for l in lessons_data}

    completed_lessons = []
    total_score    = 0
    total_possible = 0

    for p in user_progress:
        lesson        = lessons_map.get(p.lesson_id, {})
        score_percent = round((p.score / p.total) * 100) if p.total > 0 else 0
        total_score   += p.score
        total_possible += p.total

        completed_lessons.append({
            'title':         lesson.get('title', 'Unknown lesson'),
            'theme':         lesson.get('theme', ''),
            'score':         p.score,
            'total':         p.total,
            'score_percent': score_percent,
            'completed_at':  p.completed_at.strftime('%d %b %Y') if p.completed_at else ''
        })

    avg_score     = round((total_score / total_possible) * 100) if total_possible > 0 else 0
    words_learned = sum(
        len(lessons_map[p.lesson_id]['word_ids'])
        for p in user_progress
        if p.lesson_id in lessons_map
    )

    stats = {
        'lessons_completed': len(completed_lessons),
        'words_learned':     words_learned,
        'avg_score':         avg_score
    }

    streak = UserStreak.query.filter_by(user_id=current_user.id).first()
    streak_data = {
        'current': streak.current_streak if streak else 0,
        'longest': streak.longest_streak if streak else 0
    }

    return render_template('progress.html',
                           authenticated=True,
                           stats=stats,
                           streak=streak_data,
                           completed_lessons=completed_lessons)

@app.route('/api/my-streak')
@csrf.exempt
def my_streak():
    if not current_user.is_authenticated:
        return jsonify({'current_streak': 0, 'longest_streak': 0})
    
    streak = UserStreak.query.filter_by(user_id=current_user.id).first()

    if not streak:
        return jsonify({'current_streak': 0, 'longest_streak': 0})
    
    # Check if streak is still active

    today = datetime.utcnow().date()
    last_active = streak.last_active.date() if streak.last_active else None 

    if last_active and (today -last_active).days > 1:
        # Streak is broken - reset it 
        streak.current_streak = 0 
        db.session.commit()
    return jsonify({
        'current_streak': streak.current_streak,
        'longest_streak': streak.longest_streak,
        'last_active': str(last_active) if last_active else None
    })

# ── run ───────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)