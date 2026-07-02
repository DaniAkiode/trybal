let score = 0;
let currentQuestion = 0;
const totalQuestions = document.querySelectorAll('.question-card').length;

updateProgress();

function handleAnswer(button) {
    const index = button.dataset.index;
    const chosen = button.dataset.choice;
    const correct = button.dataset.correct;

    // Read cultural note from the hidden element in the card
    const card = button.closest('.question-card')
    const culturalNote = card.querySelector('.cultural-note-data').textContent;

    // Disable all buttons so user can't change answer
    const allButtons = document.querySelectorAll(`#choices-${index} .choice-btn`);
    allButtons.forEach(btn => btn.disabled = true);

    const feedbackEl = document.getElementById(`feedback-${index}`);
    const resultEl = document.getElementById(`result-${index}`);
    const noteEl = document.getElementById(`note-${index}`);

    if (chosen === correct) {
        score++;
        button.classList.add('correct');
        resultEl.textContent = 'Correct!';
        resultEl.className = 'feedback-result feedback-correct';
    } else {
        button.classList.add('wrong');
        resultEl.textContent = 'Not quite — the answer is: ' + correct;
        resultEl.className = 'feedback-result feedback-wrong';

        // Highlight the correct answer so the user learns
        allButtons.forEach(btn => {
            if (btn.dataset.choice === correct) {
                btn.classList.add('correct');
            }
        });
    }

    noteEl.textContent = culturalNote;
    feedbackEl.classList.remove('hidden');
    feedbackEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function nextQuestion(button) {
    const currentIndex = parseInt(button.dataset.current);
    const total        = parseInt(button.dataset.total);
    const lessonId     = parseInt(button.dataset.lesson);

    const cards = document.querySelectorAll('.question-card');

    if (currentIndex >= total - 1) {
        showResults(total, lessonId);
        return;
    }

    cards[currentIndex].classList.add('hidden');
    currentQuestion = currentIndex + 1;
    cards[currentQuestion].classList.remove('hidden');

    updateProgress();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress() {
    const percent = Math.round((currentQuestion / totalQuestions) * 100);
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent =
        'Question ' + (currentQuestion + 1) + ' of ' + totalQuestions;
}

function showResults(total, lessonId) {
    document.getElementById('quizStage').classList.add('hidden');

    const key = 'quiz_score_lesson_' + lessonId;
    localStorage.setItem(key, JSON.stringify({
        score: score,
        total: total,
        date: new Date().toISOString()
    }));

    // Save completion to localStorage for guests
    const completed = JSON.parse(localStorage.getItem('completedLessons') || '[]');
    if (!completed.includes(lessonId)) {
        completed.push(lessonId);
        localStorage.setItem('completedLessons', JSON.stringify(completed));
    }

    // Save completion to database for logged-in users
    fetch('/api/complete-lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            lesson_id: lessonId,
            score: score,
            total: total
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.current_streak && data.current_streak > 0) {
            showStreakMessage(data.current_streak);
        }
    });

    const percent = Math.round((score / total) * 100);
    let message = '';
    if (percent === 100) {
        message = 'Perfect score. You carry these words with you now.';
    } else if (percent >= 66) {
        message = 'Strong work. Review the ones you missed and try again.';
    } else {
        message = "Keep going. Every word you miss is a word you're learning.";
    }

    document.getElementById('resultsScore').textContent = score + ' / ' + total;
    document.getElementById('resultsMessage').textContent = message;
    document.getElementById('resultsScreen').classList.remove('hidden');

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showStreakMessage(streakCount) {
    const resultsContent = document.querySelector('.results-content');
    if (!resultsContent) return;

    const existing = document.getElementById('streak-message');
    if (existing) existing.remove();

    const streakEl = document.createElement('div')
    streakEl.id = 'streak-message';
    streakEl.className = 'streak-message';

    const emoji = streakCount >=7 ? '🔥' : '⚡';
    streakEl.innerHTML = `
        <p class="streak-message-number">${emoji} ${streakCount} day streak</p>
        <p class="streak-message-text">${getStreakMessage(streakCount)}</p>`;
    resultsContent.appendChild(streakEl);
}

function getStreakMessage(count) {
    if (count === 1) return "You've started your journey. Come back tomorrow to build your streak.";
    if (count < 3)  return "Two days in. You're building a habit.";
    if (count < 7)  return "You're on a roll. Keep going.";
    if (count < 14) return "A full week. Your ancestors would be proud.";
    if (count < 30) return "Two weeks strong. This is who you are now.";
    return "A month of learning. Ìwà pẹ̀lẹ́ — gentle persistence — is the highest virtue.";
}