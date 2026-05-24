// progress.js
// Handles reading and writing lesson progress to localStorage

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

function markCompletedLessonsOnScreen(){
    const completed = getCompletedLessons();

    completed.forEach(lessonsId => {
        const badge = document.getElementById(`complete-${lessonsId}`);
        if (badge) {
            badge.classList.remove('hidden');
        }

        // Change the Start button ro Review
        const btn = document.getElementById(`lesson-btn-${lessonsId}`);
        if (btn) {
            btn.textContent = 'Review';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
        }
        const card = document.querySelector(`[data-lesson-id="${lessonsId}"]`);
        if (card) {
            card.classList.add('lesson-card-complete');
        }
    });
}

// Run when the page loads
document.addEventListener('DOMContentLoaded', markCompletedLessonsOnScreen);
