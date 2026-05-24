from flask import Flask, render_template, jsonify
import json
import os
import random 
app = Flask(__name__)

# --helper ---------

def load_json(filename):
    """Load a JSON file from the data/ folder"""
    path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
    

# --routes ---------

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
    lessons_data =  load_json('yoruba_lessons.json')
    return jsonify(lessons_data['lessons'])

@app.route('/lesson/<int:lesson_id>')
def lessons(lesson_id):
    # Load both data files 
    all_words = load_json('yoruba.json')['words']
    lessons_data = load_json('yoruba_lessons.json')['lessons']

    # Find the lesson that matches the ID in the URL
    current_lesson = None 
    for l in lessons_data:
        if l['id'] == lesson_id:
            current_lesson = l
            break
    # if no lesson found, show a 404 error
    if current_lesson is None:
        return "Lesson not found", 404
    
    # Get only the words that belong to this lesson
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

    # Find the lesson 
    current_lesson = None
    for l in lessons_data:
        if l['id'] == lesson_id:
            current_lesson = l
            break
    if current_lesson is None:
        return "Lesson not found", 404
    
    # Get this lesson's words 
    word_ids = current_lesson['word_ids']
    lesson_words = [w for w in all_words if w['id'] in word_ids]

    # Build quiz questions — one per word
    questions = []
    for word in lesson_words:

        # Get 3 distractor transaltions from OTHER words 
        other_words = [w for w in all_words if w['id'] not in word_ids]
        distractors = random.sample(other_words, 3)
        wrong_answers = [d['translation'] for d in distractors]

        # Build the 4 choices and shuffle them
        choices = wrong_answers + [word['translation']]
        random.shuffle(choices)

        questions.append({
            'word': word['word'],
            'pronunciation': word['pronunciation'],
            'correct': word['translation'],
            'cultural_note': word['cultural_note'],
            'choices': choices
        })
    return render_template(
        'quiz.html',
        lesson=current_lesson, 
        questions=questions
    )




# --run ----------

if __name__ == '__main__':
    app.run(debug=False)