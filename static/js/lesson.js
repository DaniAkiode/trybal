// Track which word we're currently showing
let currentIndex = 0;
const cards = document.querySelectorAll('.word-card');
const totalWords = cards.length;

// Run once on page load to set the initial progress bar
updateProgress();

function nextWord() {
    // Hide the current card
    cards[currentIndex].classList.add('hidden');

    // Move to the next one
    currentIndex++;

    // Show the next card
    cards[currentIndex].classList.remove('hidden');

    // Update the progress bar and counter
    updateProgress();

    // Scroll to top smoothly so the word is always visible
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateProgress() {
    // Calculate percentage complete
    const percent = Math.round((currentIndex / totalWords) * 100);

    // Update the green progress bar width
    document.getElementById('progressFill').style.width = percent + '%';

    // Update the "Word 1 of 3" text
    document.getElementById('progressText').textContent =
        'Word ' + (currentIndex + 1) + ' of ' + totalWords;
}

function completeLesson(lessonId) {
    // Save completion to localStorage
    const completed = JSON.parse(localStorage.getItem('completedLessons') || '[]');

    if (!completed.includes(Number(lessonId))) {
        completed.push(Number(lessonId));
        localStorage.setItem('completedLessons', JSON.stringify(completed));
    }

    // Go back to home
    window.location.href = '/';
}