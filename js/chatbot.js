// Dummy chatbot logic
document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chatbotToggle');
    const chatWindow = document.getElementById('chatbotWindow');
    const chatClose = document.getElementById('chatClose');
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    if (chatToggle) {
        chatToggle.onclick = () => chatWindow.classList.toggle('open');
    }
    if (chatClose) {
        chatClose.onclick = () => chatWindow.classList.remove('open');
    }

    function addMessage(text, isBot = true) {
        const msg = document.createElement('div');
        msg.className = `message ${isBot ? 'bot' : 'user'}`;
        msg.innerHTML = `<div class="msg-bubble">${text}</div>`;
        chatMessages.appendChild(msg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (chatSend) {
        chatSend.onclick = () => {
            const val = chatInput.value.trim();
            if (!val) return;
            addMessage(val, false);
            chatInput.value = '';
            setTimeout(() => addMessage("I'm JanBot, your digital assistant. I've received your query and will guide you through the process."), 600);
        };
        if (chatInput) {
            chatInput.addEventListener("keypress", function(e) {
                if (e.key === "Enter") chatSend.onclick();
            });
        }
    }

    // Initial message
    if (chatMessages && chatMessages.children.length === 0) {
        addMessage("Namaste! I am JanBot. I can help you file grievances, track status, and answer questions about JanSamadhan. How can I help you today?");
    }
});
