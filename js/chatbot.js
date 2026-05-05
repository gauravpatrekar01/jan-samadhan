// Smart Grievance Chatbot – Modern UI Integration
const ChatBotLogic = {
    // 1. Complaint Categories
    categories: {
        'Electricity': ['power', 'voltage', 'electricity', 'outage', 'cut', 'power cut', 'light'],
        'Water Supply': ['water', 'leakage', 'pressure', 'pipeline', 'supply', 'no water'],
        'Sanitation': ['garbage', 'drainage', 'cleanliness', 'waste', 'smell', 'sewer', 'blockage', 'dustbin'],
        'Roads': ['pothole', 'road', 'damage', 'repair', 'construction'],
        'Street Lights': ['street light', 'lamp', 'dark road', 'light not working']
    },
    
    // Intents mapping
    intents: {
        'Action Request': ['register complaint', 'file a complaint', 'submit complaint', 'update status', 'fix my complaint', 'record complaint', 'register', 'submit'],
        'Frustrated': ['frustrated', 'angry', 'terrible', 'worst', 'hate', 'too slow', 'upset', 'annoyed'],
        'FAQ_Steps': ['how to file', 'how can i file', 'how to report', 'steps to file', 'how to register'],
        'FAQ_Status': ['how to track', 'check status', 'track status', 'where is my complaint'],
        'FAQ_Escalate': ['not resolved', 'what if unresolved', 'what to do if unresolved', 'unresolved'],
        'FAQ_Feedback': ['give feedback', 'how to give feedback']
    },

    analyze(text) {
        text = text.toLowerCase();
        let matchIntent = null;
        for (let [intKey, keywords] of Object.entries(this.intents)) {
            if (keywords.some(kw => text.includes(kw))) {
                matchIntent = intKey;
                break;
            }
        }
        let matchedCat = null;
        let maxHits = 0;
        for (let [cat, keywords] of Object.entries(this.categories)) {
            let hits = keywords.filter(kw => text.includes(kw)).length;
            if (hits > maxHits) {
                maxHits = hits;
                matchedCat = cat;
            }
        }
        return { category: matchedCat, intent: matchIntent };
    },

    generateResponse(text) {
        if (!text || text.trim().length <= 3) {
            return "Could you please provide more details about your issue so I can guide you better?";
        }
        const analysis = this.analyze(text);
        if (analysis.intent === 'Frustrated') return "I understand this can be frustrating. Let me guide you on how you can get this resolved. Please tell me what issue you are facing.";
        if (analysis.intent === 'Action Request') return "I’m here to guide you, but I’m unable to register or update complaints directly. You can use the official platform to proceed.";
        if (analysis.intent === 'FAQ_Steps') return "**Steps to file:**\n1. Identify the issue.\n2. Mention your location.\n3. Describe the problem clearly.\n4. Submit via the official portal.";
        if (analysis.intent === 'FAQ_Status') return "To track your status, simply use the official portal's tracking tools with your Complaint ID!";
        if (analysis.intent === 'FAQ_Escalate') return "If your issue remains unresolved, you can escalate it to a higher authority physically or via the official helpline.";
        if (analysis.intent === 'FAQ_Feedback') return "You can peacefully provide feedback directly on the official platform once your issue is marked as resolved.";
        
        if (analysis.category) {
            return `I understand your concern. This seems to be a **${analysis.category}** issue. You can report it through your local municipal portal or helpline by providing your location and issue details.`;
        }
        return "I’m here to help with information regarding civic issues. Please describe your concern.";
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chatbotToggle');
    const chatWindow = document.getElementById('chatbotWindow');
    const chatClose = document.getElementById('chatClose');
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    if (chatToggle) {
        chatToggle.onclick = () => {
            chatWindow.classList.toggle('open');
            if (chatWindow.classList.contains('open') && chatInput) {
                setTimeout(() => chatInput.focus(), 300);
            }
        };
    }
    if (chatClose) chatClose.onclick = () => chatWindow.classList.remove('open');

    // Simple Markdown parser for headings, bold, and lists
    function parseMarkdown(text) {
        // Convert numbered lists
        text = text.replace(/(?:\r\n|\r|\n|^)(\d+\.\s+)(.*?)(?=\n|$)/g, '<div class="list-item"><span class="list-number">$1</span>$2</div>');
        // Convert headings (Summary, Steps, etc.)
        text = text.replace(/(?:\r\n|\r|\n|^)(Summary|Steps to resolve|Required documents if any|Next action)(:?)(?=\n|$)/gi, '<div class="chat-heading">$1$2</div>');
        // Convert bold text
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Convert newlines to breaks
        text = text.replace(/\n/g, '<br/>');
        return text;
    }

    // Formats the current time
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        let minutes = now.getMinutes();
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        return `${hours}:${minutes} ${ampm}`;
    }

    let typingIndicatorElement = null;

    function showTypingIndicator() {
        if (typingIndicatorElement) return;
        
        typingIndicatorElement = document.createElement('div');
        typingIndicatorElement.className = 'message bot typing';
        typingIndicatorElement.innerHTML = `
            <div class="chat-avatar">🤖</div>
            <div class="msg-bubble loader-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatMessages.appendChild(typingIndicatorElement);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        if (typingIndicatorElement) {
            typingIndicatorElement.remove();
            typingIndicatorElement = null;
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addMessage(text, type = 'bot') { // type: 'user', 'bot', 'error'
        const msg = document.createElement('div');
        msg.className = `message ${type}`;
        
        const avatar = type === 'user' ? '👤' : (type === 'error' ? '⚠️' : '🤖');
        const formattedText = type === 'user' ? text : parseMarkdown(text);
        
        let innerHTML = '';
        
        if (type !== 'user') {
            innerHTML += `<div class="chat-avatar">${avatar}</div>`;
        }

        innerHTML += `
            <div class="msg-content">
                <div class="msg-bubble">${formattedText}</div>
                <div class="msg-time">${getCurrentTime()}</div>
            </div>
        `;

        if (type === 'user') {
            innerHTML += `<div class="chat-avatar user-avatar">${avatar}</div>`;
        }

        msg.innerHTML = innerHTML;
        chatMessages.appendChild(msg);
        scrollToBottom();
    }

    async function handleSend(retryVal = null) {
        const val = retryVal || chatInput.value.trim();
        if (!val) return;
        
        if (!retryVal) {
            addMessage(val, 'user');
            chatInput.value = '';
        }

        showTypingIndicator();

        try {
            if (window.JanSamadhanAPI?.chatbotQuery) {
                const result = await window.JanSamadhanAPI.chatbotQuery(val);
                const answer = result?.answer || result?.data?.answer || result?.response;
                hideTypingIndicator();
                
                if (answer) {
                    addMessage(answer, 'bot');
                    return;
                }
            }
        } catch (error) {
            console.warn('Chatbot API unavailable or failed:', error);
            hideTypingIndicator();
            
            // Show error message with retry
            const errorMsg = document.createElement('div');
            errorMsg.className = `message error`;
            errorMsg.innerHTML = `
                <div class="chat-avatar">⚠️</div>
                <div class="msg-content">
                    <div class="msg-bubble">
                        Sorry, I encountered an error connecting to the server.
                        <button class="retry-btn">Retry</button>
                    </div>
                </div>
            `;
            const retryBtn = errorMsg.querySelector('.retry-btn');
            retryBtn.onclick = () => {
                errorMsg.remove();
                handleSend(val);
            };
            chatMessages.appendChild(errorMsg);
            scrollToBottom();
            return;
        }

        // Fallback local logic
        hideTypingIndicator();
        setTimeout(() => {
            const botResponse = ChatBotLogic.generateResponse(val);
            addMessage(botResponse, 'bot');
        }, 400);
    }

    if (chatSend) {
        chatSend.onclick = () => handleSend();
        if (chatInput) {
            chatInput.addEventListener("keypress", function(e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    handleSend();
                }
            });
        }
    }

    const suggestions = document.querySelectorAll('.chat-suggestion');
    suggestions.forEach(btn => {
        btn.onclick = () => {
            if(chatInput) {
                chatInput.value = btn.textContent;
                chatSend.onclick();
            }
        };
    });

    if (chatMessages && chatMessages.children.length === 0) {
        setTimeout(() => {
            addMessage("**Welcome to JanBot!** 👋\n\nI am your AI assistant for the JanSamadhan platform.\n\nI can help you:\n1. Understand the grievance process\n2. Answer FAQs\n3. Provide tracking instructions\n\nHow can I help you today?", 'bot');
        }, 500);
    }
});
