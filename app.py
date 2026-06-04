from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from datetime import datetime
import json
import os
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ── configuration ────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

import re 

database_url = os.environ.get('DATABASE_URL', 'sqlite://trybal.db')

# Render provides postgres:// but SQLAlchemy requires postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

# ── initialise extensions ────────────────────────────────
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

# ── create database tables ───────────────────────────────
with app.app_context():
    db.create_all()

# ── helper ───────────────────────────────────────────────
def load_json(filename):
    """Load a JSON file from the data/ folder."""
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ── routes ───────────────────────────────────────────────
@app.route('/')
def index():
    lessons_data = load_json('yoruba_lessons.json')
    return render_template('index.html', lessons=lessons_data['lessons'])

@app.route('/api/words')
def get_words():
    words_data = load_json('yoruba.json')
    return jsonify(words_data['words'])

@app.route('/api/lessons')
def get_lessons():
    lessons_data = load_json('yoruba_lessons.json')
    return jsonify(lessons_data['lessons'])

@app.route('/lesson/<int:lesson_id>')
def lessons(lesson_id):
    all_words    = load_json('yoruba.json')['words']
    lessons_data = load_json('yoruba_lessons.json')['lessons']

    current_lesson = None
    for l in lessons_data:
        if l['id'] == lesson_id:
            current_lesson = l
            break

    if current_lesson is None:
        return "Lesson not found", 404

    word_ids = current_lesson['word_ids']
    lessons_words = [word for word in all_words if word['id'] in word_ids]

    return render_template(
        'lesson.html',
        lesson=current_lesson,
        words=lessons_words
    )

@app.route('/quiz/<int:lesson_id>')
def quiz(lesson_id):
    all_words = load_json('yoruba.json')['words']
    lessons_data = load_json('yoruba_lessons.json')['lessons']

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
        other_words  = [w for w in all_words if w['id'] not in word_ids]
        distractors  = random.sample(other_words, 3)
        wrong_answers = [d['translation'] for d in distractors]
        choices      = wrong_answers + [word['translation']]
        random.shuffle(choices)

        questions.append({
            'word':          word['word'],
            'pronunciation': word['pronunciation'],
            'correct':       word['translation'],
            'cultural_note': word['cultural_note'],
            'choices':       choices
        })

    return render_template(
        'quiz.html',
        lesson=current_lesson,
        questions=questions
    )

@app.route('/api/my-progress')
def my_progress():
    if current_user.is_authenticated:
        completed = UserProgress.query.filter_by(
            user_id=current_user.id,
            completed=True
        ).all()
        lesson_ids = [p.lesson_id for p in completed]
        return jsonify({'completedLessons': lesson_ids, 'source': 'database'})
    else:
        completed = []
        return jsonify({'completedLessons': completed, 'source': 'guest'})

@app.route('/api/complete-lesson', methods=['POST'])
def complete_lesson():
    if not current_user.is_authenticated:
        return jsonify({'status': 'guest'})

    data = request.get_json()
    lesson_id = data.get('lesson_id')
    score = data.get('score', 0)
    total = data.get('total', 0)

    existing = UserProgress.query.filter_by(
        user_id   = current_user.id,
        lesson_id = lesson_id
    ).first()

    if existing:
        existing.score = score
        existing.total = total
        existing.completed = True
        existing.completed_at = datetime.utcnow()
    else:
        progress = UserProgress(
            user_id = current_user.id,
            lesson_id = lesson_id,
            completed = True,
            score = score,
            total = total,
            completed_at = datetime.utcnow()
        )
        db.session.add(progress)

    db.session.commit()
    return jsonify({'status': 'ok'})
# ── run ──────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)