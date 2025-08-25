document.addEventListener('DOMContentLoaded', function () {
    const gad7Form = document.getElementById('gad7-form');
    const submitGad7Btn = document.getElementById('submit-gad7');
    const gad7ResultDiv = document.getElementById('gad7-result');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatBox = document.getElementById('chat-box');

    // Global variables to store the assessment results
    let gad7Score = 0;
    let gad7Level = 'not assessed';
    // NOTE: Getting real-time emotion from the video stream to JS is complex.
    // We will let the backend handle the context.
    let currentEmotion = 'not detected';

    // --- GAD-7 Assessment Logic ---
    const gad7Questions = [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it is hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid as if something awful might happen"
    ];

    function buildGAD7Form() {
        gad7Questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('question');
            questionDiv.innerHTML = `
                <label for="q${index}">${index + 1}. ${question}</label>
                <select name="q${index}" id="q${index}">
                    <option value="0">Not at all</option>
                    <option value="1">Several days</option>
                    <option value="2">More than half the days</option>
                    <option value="3">Nearly every day</option>
                </select>
            `;
            gad7Form.appendChild(questionDiv);
        });
    }

    function calculateGAD7Score() {
        let totalScore = 0;
        for (let i = 0; i < gad7Questions.length; i++) {
            const select = document.getElementById(`q${i}`);
            totalScore += parseInt(select.value, 10);
        }

        let interpretation = '';
        if (totalScore <= 4) interpretation = 'Minimal anxiety';
        else if (totalScore <= 9) interpretation = 'Mild anxiety';
        else if (totalScore <= 14) interpretation = 'Moderate anxiety';
        else interpretation = 'Severe anxiety';
        
        // Update global variables
        gad7Score = totalScore;
        gad7Level = interpretation;

        gad7ResultDiv.innerHTML = `<strong>Your Score: ${totalScore}</strong><p>${interpretation}. This result is not a diagnosis. Please consult a healthcare professional for a proper assessment.</p>`;
        gad7ResultDiv.style.display = 'block';
    }

    // --- Chatbot Logic ---
    async function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (userMessage === "") return;

        appendMessage(userMessage, 'user');
        chatInput.value = "";

        // **MODIFICATION HERE: Send GAD-7 score and level to the backend**
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage,
                    emotion: currentEmotion, // Placeholder for now
                    gad7Score: gad7Score,
                    gad7Level: gad7Level
                }),
            });

            const data = await response.json();
            appendMessage(data.reply, 'bot');

        } catch (error) {
            console.error('Error:', error);
            appendMessage("Sorry, I'm having trouble connecting. Please try again later.", 'bot');
        }
    }

    function appendMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        // A simple way to format line breaks from the bot
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Event Listeners
    buildGAD7Form();
    submitGad7Btn.addEventListener('click', calculateGAD7Score);
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});