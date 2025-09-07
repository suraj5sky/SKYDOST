const chatContainer = document.getElementById("chat-container");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const typingIndicator = document.getElementById("typing-indicator");
const sendButton = document.getElementById("send-button");
const clearChatButton = document.getElementById("clear-chat");
const voiceButton = document.getElementById("voice-button");
const voiceToggle = document.getElementById("voice-toggle");
const voiceStatus = document.getElementById("voice-status");
const modeElements = document.querySelectorAll(".mode");
const helpButton = document.getElementById("help-button");
const helpModal = document.getElementById("help-modal");

let currentMode = "general";
let isListening = false;
let recognition = null;

// Check if browser supports Speech Recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        chatForm.dispatchEvent(new Event("submit"));
    };
    
    recognition.onerror = function(event) {
        console.error('Speech recognition error', event.error);
        appendMessage("bot", "Sorry, I couldn't hear you clearly. Please try again.");
        stopVoiceRecognition();
    };
    
    recognition.onend = function() {
        stopVoiceRecognition();
    };
} else {
    // Browser doesn't support speech recognition
    voiceButton.style.display = 'none';
    voiceToggle.style.display = 'none';
}

// Toggle help modal
helpButton.addEventListener("click", () => {
    helpModal.style.display = helpModal.style.display === 'block' ? 'none' : 'block';
});

// Close help modal when clicking outside
document.addEventListener("click", (e) => {
    if (!helpModal.contains(e.target) && e.target !== helpButton) {
        helpModal.style.display = 'none';
    }
});

// Function to start voice recognition
function startVoiceRecognition() {
    if (recognition) {
        try {
            recognition.start();
            isListening = true;
            voiceButton.classList.add('listening');
            voiceStatus.classList.add('active');
            voiceStatus.innerHTML = '<i class="fas fa-microphone"></i> <span>Listening...</span>';
            userInput.placeholder = "I'm listening...";
        } catch (error) {
            console.error('Speech recognition start failed', error);
        }
    }
}

// Function to stop voice recognition
function stopVoiceRecognition() {
    isListening = false;
    voiceButton.classList.remove('listening');
    voiceStatus.classList.remove('active');
    voiceStatus.innerHTML = '<i class="fas fa-microphone-slash"></i> <span>Voice: Off</span>';
    userInput.placeholder = "Ask me anything about your studies...";
}

// Toggle voice recognition
voiceButton.addEventListener("click", () => {
    if (!recognition) return;
    
    if (isListening) {
        recognition.stop();
        stopVoiceRecognition();
    } else {
        startVoiceRecognition();
    }
});

// Voice toggle button
voiceToggle.addEventListener("click", () => {
    if (!recognition) return;
    
    if (isListening) {
        recognition.stop();
        stopVoiceRecognition();
        voiceToggle.innerHTML = '<i class="fas fa-microphone"></i> Voice';
    } else {
        startVoiceRecognition();
        voiceToggle.innerHTML = '<i class="fas fa-microphone-slash"></i> Stop';
    }
});

// Handle mode selection
modeElements.forEach(mode => {
    mode.addEventListener("click", () => {
        // Remove active class from all modes
        modeElements.forEach(m => m.classList.remove('active'));
        
        // Add active class to clicked mode
        mode.classList.add('active');
        
        // Set current mode
        currentMode = mode.dataset.mode;
        
        // Send mode change message
        let modeMessage = "";
        switch(currentMode) {
            case "subject":
                modeMessage = "📘 Subject Mode activated! What subject would you like help with?";
                break;
            case "quiz":
                modeMessage = "🧩 Quiz Mode activated! Let's test your knowledge. What topic would you like a quiz on?";
                break;
            case "motivation":
                modeMessage = "🌱 Motivation Mode activated! Need some inspiration or encouragement?";
                break;
            default:
                modeMessage = "💬 General Chat mode activated! How can I help you today?";
        }
        
        appendMessage("bot", modeMessage);
        
        // Send mode change to server
        fetch("/mode", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ mode: currentMode })
        }).catch(error => {
            console.error("Mode change error:", error);
        });
    });
});

// Function to append messages to chat container
function appendMessage(sender, message, provider = null) {
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
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
                <div class="time">${timeString}</div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="sender">You</div>
                <div class="text">${message}</div>
                <div class="time">${timeString}</div>
            </div>
            <div class="avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
    }
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll
}

// Handle form submission
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userMessage = userInput.value.trim();
    if (!userMessage) return;

    appendMessage("user", userMessage);
    userInput.value = "";
    userInput.focus();
    
    // Disable send button during request
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    
    typingIndicator.style.display = "flex";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                message: userMessage,
                mode: currentMode 
            })
        });

        const data = await response.json();
        typingIndicator.style.display = "none";
        
        // Re-enable send button
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';

        if (data.answer) {
            appendMessage("bot", data.answer);
        } else if (data.error) {
            appendMessage("bot", "Sorry, I encountered an error. Please try again.");
        }
    } catch (error) {
        typingIndicator.style.display = "none";
        
        // Re-enable send button
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        
        appendMessage("bot", "Sorry, I'm having trouble connecting. Please check your connection and try again.");
        console.error("Chat error:", error);
    }
});

// Display current mode status
async function displayStatus() {
    try {
        const response = await fetch("/status");
        const data = await response.json();
        
        const statusElement = document.createElement("div");
        statusElement.classList.add("status-message");
        
        let statusHTML = `<div>AI Assistant Ready`;
        
        if (!data.any_provider_available) {
            statusHTML = `<div>Basic Mode (Limited Features)`;
        }
        
        statusHTML += '</div>';
        statusElement.innerHTML = statusHTML;
        
        // Insert at the beginning of chat container
        chatContainer.insertBefore(statusElement, chatContainer.firstChild);
    } catch (error) {
        console.log("Could not load status:", error);
    }
}

// Call status display when page loads
window.addEventListener("load", () => {
    displayStatus();
    userInput.focus();
});

// Clear chat history
clearChatButton.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear the conversation?")) {
        try {
            const response = await fetch("/clear", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            
            if (response.ok) {
                // Clear the chat UI but keep the welcome message and status
                const messages = chatContainer.querySelectorAll('.message:not(.welcome)');
                messages.forEach(msg => msg.remove());
                
                // Re-display status
                displayStatus();
                
                // Add a confirmation message
                appendMessage("bot", "Conversation cleared. How can I help you with your studies today?");
            }
        } catch (error) {
            console.error("Clear chat error:", error);
        }
    }
});

// Allow sending message with Enter key
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event("submit"));
    }
});

// Auto-resize textarea (if we change to textarea later)
userInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
});

// Focus input on load
window.addEventListener("load", () => {
    userInput.focus();
});