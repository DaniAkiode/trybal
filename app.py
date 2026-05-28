from flask import Flask, render_template, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
import json
import os
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ── configuration ────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trybal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable is not set.")

# ── initialise extensions ────────────────────────────────
from models import db, User, UserProgress, UserStreak

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

    word_ids     = current_lesson['word_ids']
    lessons_words = [word for word in all_words if word['id'] in word_ids]

    return render_template(
        'lesson.html',
        lesson=current_lesson,
        words=lessons_words
    )

@app.route('/quiz/<int:lesson_id>')
def quiz(lesson_id):
    all_words    = load_json('yoruba.json')['words']
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

# ── run ──────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)