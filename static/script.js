const chatContainer = document.getElementById("chat-container");
const userInput = document.getElementById("user-input");
const typingIndicator = document.getElementById("typing-indicator");
const sendButton = document.getElementById("send-button");
const clearChatButton = document.getElementById("clear-chat");
const voiceToggle = document.getElementById("voice-toggle");
const modeElements = document.querySelectorAll(".mode");

let currentMode = "general";

// Handle mode selection
modeElements.forEach(mode => {
    mode.addEventListener("click", () => {
        // Remove active class from all modes
        modeElements.forEach(m => m.classList.remove('active'));
        
        // Add active class to clicked mode
        mode.classList.add('active');
        
        // Set current mode
        currentMode = mode.dataset.mode;
        
        // Send mode change to backend
        fetch('/mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mode: currentMode })
        });
        
        // Show mode change message
        let modeMessage = "";
        switch(currentMode) {
            case "subject":
                modeMessage = "📘 Subject Mode activated! What subject would you like help with?";
                break;
            case "informative":
                modeMessage = "🧩 Informative Mode activated! I'll provide detailed explanations and insights. What would you like to learn about?";
                break;
            case "motivation":
                modeMessage = "🌱 Motivation Mode activated! Need some inspiration or encouragement to keep studying?";
                break;
            default:
                modeMessage = "💬 General Chat mode activated! How can I help you today?";
        }
        
        appendMessage("bot", modeMessage);
    });
});

// Function to append messages to chat container
function appendMessage(sender, message) {
    // Remove welcome message if it's the first user message
    const welcomeContainer = document.querySelector('.welcome-container');
    if (welcomeContainer && sender === "user") {
        welcomeContainer.remove();
    }
    
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    
    if (sender === "bot") {
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="sender">SKY Dost</div>
                <div class="text">${message}</div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
                <div class="sender">You</div>
                <div class="text">${message}</div>
            </div>
        `;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll
}

// Handle form submission
sendButton.addEventListener("click", async (e) => {
    e.preventDefault();
    const userMessage = userInput.value.trim();
    if (!userMessage) return;

    appendMessage("user", userMessage);
    userInput.value = "";
    userInput.style.height = "auto";
    userInput.focus();
    
    // Disable send button during request
    sendButton.disabled = true;
    
    typingIndicator.style.display = "flex";
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        // Make API call to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: userMessage,
                mode: currentMode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Display the response from the backend (without provider info)
            appendMessage("bot", data.answer);
        } else {
            // Handle error
            appendMessage("bot", "Sorry, I'm having trouble connecting right now. Please try again later.");
            console.error("API Error:", data.error);
        }
    } catch (error) {
        // Handle network error
        appendMessage("bot", "Network error. Please check your connection and try again.");
        console.error("Network Error:", error);
    } finally {
        // Hide typing indicator and re-enable send button
        typingIndicator.style.display = "none";
        sendButton.disabled = false;
    }
});


// Allow sending message with Enter key
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendButton.click();
    }
});

// Auto-resize textarea
userInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
});

// Clear chat history
clearChatButton.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear the conversation?")) {
        try {
            // Call backend to clear chat
            await fetch('/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            // Clear the chat UI
            chatContainer.innerHTML = '';
            
            // Add welcome message back
            const welcomeContainer = document.createElement('div');
            welcomeContainer.className = 'welcome-container';
            welcomeContainer.innerHTML = `
                <h1 class="welcome-title">Hello, I'm SKY Dost</h1>
                <p class="welcome-subtitle">Your study friend and assistant</p>
                
                <div class="capabilities">
                    <div class="capability">
                        <i class="fas fa-book"></i>
                        <h3>Subject Help</h3>
                        <p>Get explanations for any subject or topic you're studying</p>
                    </div>
                    <div class="capability">
                        <i class="fas fa-lightbulb"></i>
                        <h3>Informative Content</h3>
                        <p>Learn with detailed explanations and examples</p>
                    </div>
                    <div class="capability">
                        <i class="fas fa-heart"></i>
                        <h3>Motivation</h3>
                        <p>Get encouragement and study tips to stay focused</p>
                    </div>
                    <div class="capability">
                        <i class="fas fa-graduation-cap"></i>
                        <h3>Study Plans</h3>
                        <p>Create customized study schedules and plans</p>
                    </div>
                </div>
                
                <p>How can I help with your studies today?</p>
            `;
            
            chatContainer.appendChild(welcomeContainer);
        } catch (error) {
            console.error("Error clearing chat:", error);
        }
    }
});

// Check API status on load
window.addEventListener("load", async () => {
    userInput.focus();
    
    try {
        const response = await fetch('/status');
        const status = await response.json();
        
        if (!status.any_provider_available) {
            appendMessage("bot", "⚠️ Note: Running in basic mode. Add API keys to enable AI providers.", "system");
        }
    } catch (error) {
        console.error("Error checking status:", error);
    }
});