// Smart Grievance Chatbot – Informational Knowledge Base (Kind & Polite Mode)
const ChatBotLogic = {
    // 1. Complaint Categories
    categories: {
        'Electricity': ['power', 'voltage', 'electricity', 'outage', 'cut', 'power cut', 'light'],
        'Water Supply': ['water', 'leakage', 'pressure', 'pipeline', 'supply', 'no water'],
        'Sanitation': ['garbage', 'drainage', 'cleanliness', 'waste', 'smell', 'sewer', 'blockage', 'dustbin'],
        'Roads': ['pothole', 'road', 'damage', 'repair', 'construction'],
        'Street Lights': ['street light', 'lamp', 'dark road', 'light not working']
    },
    
    // Departments, Responsibilities & Timeline (For additional FAQs)
    categoryInfo: {
        'Electricity': { dept: 'Electricity Board', time: 'Few hours to 1–2 days' },
        'Water Supply': { dept: 'Water Supply Department', time: '1–3 days' },
        'Sanitation': { dept: 'Municipal Corporation', time: '1–2 days' },
        'Roads': { dept: 'PWD', time: 'Longer duration' },
        'Street Lights': { dept: 'Municipal Electrical Dept', time: 'Few days' }
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
        
        if (analysis.intent === 'Frustrated') {
            return "I understand this can be frustrating. Let me guide you on how you can get this resolved. Please tell me what issue you are facing.";
        }

        if (analysis.intent === 'Action Request') {
            return "I’m here to guide you, but I’m unable to register or update complaints. You can use the official government platform to proceed.";
        }

        if (analysis.intent === 'FAQ_Steps') {
            return `I would be happy to guide you! Please follow these steps to file:<br/><br/>
            1. Identify the issue.<br/>
            2. Mention your location.<br/>
            3. Describe the problem clearly.<br/>
            4. Submit via the official Government website, mobile app, helpline, or local office.`;
        }

        if (analysis.intent === 'FAQ_Status') {
            return "To track your status, simply use the official portal or app's tracking tools with your Complaint ID!";
        }

        if (analysis.intent === 'FAQ_Escalate') {
            return "If your issue remains unresolved, you can easily escalate it to a higher authority physically or via the official helpline.";
        }

        if (analysis.intent === 'FAQ_Feedback') {
            return "You can peacefully provide feedback directly on the official platform once your issue is marked as resolved.";
        }

        if (analysis.category) {
            if (analysis.category === 'Water Supply') {
                return "I understand your concern. This appears to be a water supply issue. You can report it through your municipal website or helpline by mentioning your area and describing the problem.";
            } else {
                return `I understand your concern. This seems to be a ${analysis.category.toLowerCase()} issue. You can report it through your local municipal portal or helpline by providing your location and issue details.`;
            }
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
        chatToggle.onclick = () => chatWindow.classList.toggle('open');
    }
    if (chatClose) {
        chatClose.onclick = () => {
            chatWindow.classList.remove('open');
        };
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
            
            setTimeout(() => {
                const botResponse = ChatBotLogic.generateResponse(val);
                addMessage(botResponse, true);
            }, 600);
        };
        if (chatInput) {
            chatInput.addEventListener("keypress", function(e) {
                if (e.key === "Enter") chatSend.onclick();
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
        addMessage("Welcome to the Smart Grievance Assistant. I’m here to guide you with information on civic issues and complaint processes.");
        setTimeout(() => {
            addMessage(`<em>I provide guidance only and cannot perform complaint registration or updates.</em>`);
        }, 100);
    }
});
