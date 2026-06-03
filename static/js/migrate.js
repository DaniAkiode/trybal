document.addEventListener('DOMContentLoaded', function() {
    const completedLessons = JSON.parse(
        localStorage.getItem('completedLessons') || '[]'
    );

    // Build scores object from localStorage
    const scores = {};
    completedLessons.forEach(lessonId => {
        const key = 'quiz_score_lesson_' + lessonId;
        const saved = localStorage.getItem(key);
        if (saved) {
            scores[lessonId] = JSON.parse(saved);
        }
    });

    // Only migrate if there's something to migrate 
    if (completedLessons.length === 0) {
        window.location.href = '/';
        return;
    }

    // Send progress to server 
    fetch('/api/migrate-progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            completedLessons: completedLessons,
            scores: scores
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // Clear localStorage now that data is safe in the database
            localStorage.removeItem('completedLessons');
            completedLessons.forEach(lessonId => {
                localStorage.removeItem('quiz_score_lesson_' + lessonId);
            });
        }
        // Redirect home regardless
        window.location.href = '/';
    })
    .catch(() => {
        // If migration fails, still go home without blocking the user
        window.location.href = '/';
    });
});