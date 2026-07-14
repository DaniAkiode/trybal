// progress.js
// Handles reading and writing lesson progress to localStorage

// Force fresh data when user navigates back to this page
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        markCompletedLessonsOnScreen();
    }
});


function getCompletedLessons() {
    return JSON.parse(localStorage.getItem('completedLessons') || '[]');
}

function markLessonComplete(lessonId) {
    const completed = getCompletedLessons();
    if (!completed.includes(Number(lessonId))) {
        completed.push(Number(lessonId));
        localStorage.setItem('completedLessons', JSON.stringify(completed));
    }
}

function isLessonComplete(lessonId) {
    return getCompletedLessons().includes(Number(lessonId));
}

function markCompletedLessonsOnScreen() {
    fetch('/api/my-progress')
        .then(response => response.json())
        .then(data => {
            // Get current language from the page if available
            const langData = document.getElementById('language-data');
            const currentLang = langData ? langData.dataset.language : null;

            let completed = [];

            if (data.source === 'database') {
                const byLang = data.completedByLanguage || {};
                if (currentLang && byLang[currentLang]) {
                    // On a language-specific page, only show that language's progress
                    completed = byLang[currentLang];
                } else if (!currentLang) {
                    // On home screen, don't show any completions
                    // (home screen shows languages, not lessons)
                    completed = [];
                }
            } else {
                // Guest — use localStorage
                completed = getCompletedLessons();
            }

            completed.forEach(lessonId => {
                const badge = document.getElementById(`complete-${lessonId}`);
                if (badge) badge.classList.remove('hidden');

                const btn = document.getElementById(`lesson-btn-${lessonId}`);
                if (btn) {
                    btn.textContent = 'Review';
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline');
                }

                const card = document.querySelector(`[data-lesson-id="${lessonId}"]`);
                if (card) card.classList.add('lesson-card-complete');
            });
        })
        .catch(() => {
            const completed = getCompletedLessons();
            completed.forEach(lessonId => {
                const badge = document.getElementById(`complete-${lessonId}`);
                if (badge) badge.classList.remove('hidden');
            });
        });
}

function loadNavStreak() {
    fetch('/api/my-streak')
        .then(response => response.json())
        .then(data => {
            if (data.current_streak > 0) {
                const streakEl = document.getElementById('nav-streak');
                const countEl  = document.getElementById('nav-streak-count');
                if (streakEl && countEl) {
                    countEl.textContent = data.current_streak;
                    streakEl.style.display = 'inline';
                }
            }
        })
        .catch(() => {});
}

document.addEventListener('DOMContentLoaded', function() {
    markCompletedLessonsOnScreen();
    loadNavStreak();
});