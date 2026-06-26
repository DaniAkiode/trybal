// audio.js
// Handles text-to-speech pronunciation for all languages

const LANGUAGE_CODES = {
    'yoruba':  'yo',
    'igbo':    'ig',
    'swahili': 'sw'
};

function speakWord(word, languageCode, btnIndex) {
    // Cancel any speech currently playing
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(word);

    // Set the language so the synthesiser uses correct phonetics
    utterance.lang = LANGUAGE_CODES[languageCode] || 'en';

    // Slow it down slightly so learners can follow
    utterance.rate = 0.85;

    // Find the right button using the index
    const btnId = btnIndex !== undefined ? `speak-btn-${btnIndex}` : 'speak-btn';
    const btn   = document.getElementById(btnId);

    if (btn) {
        btn.classList.add('speaking');
        utterance.onend = function() {
            btn.classList.remove('speaking');
        };
    }

    window.speechSynthesis.speak(utterance);
}


function handleSpeak(button) {
    const word        = button.dataset.word;
    const pronunciation = button.dataset.pronunciation;
    const index       = button.dataset.langIndex;
    const langData    = document.getElementById('language-data');
    const langCode    = langData ? langData.dataset.language : 'en';

    // For languages where TTS is poor, speak the pronunciation
    // guide in English instead of the word itself
    const poorTTSLanguages = ['yoruba', 'igbo'];
    const textToSpeak = poorTTSLanguages.includes(langCode) && pronunciation
        ? pronunciation
        : word;

    speakWord(textToSpeak, langCode, index);
}

function isSpeechSupported() {
    return 'speechSynthesis' in window;
}