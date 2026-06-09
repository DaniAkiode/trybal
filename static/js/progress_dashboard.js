document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.score-bar-fill').forEach(function(bar) {
        const percent = bar.dataset.percent;
        bar.style.width = percent + '%';
    });
});