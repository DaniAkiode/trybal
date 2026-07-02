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
    // Fetch from server — works for both logged in and guest users
    fetch('/api/my-progress')
        .then(response => response.json())
        .then(data => {
            const completed = data.completedLessons;

            // If guest, also merge localStorage
            if (data.source === 'guest') {
                const local = getCompletedLessons();
                local.forEach(id => {
                    if (!completed.includes(id)) completed.push(id);
                });
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
            // Fallback to localStorage if API fails
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