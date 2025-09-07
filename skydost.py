from flask import Flask, render_template, request, jsonify, session
import os
from dotenv import load_dotenv
import time
import random
import requests
import json
from flask_cors import CORS  # Add this import

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "sky-dost-secret-key-2023")
CORS(app)  # Add this to handle cross-origin requests

# API Keys from environment
API_KEYS = {
    "openai": os.getenv("OPENAI_KEY"),
    "groq": os.getenv("GROQ_KEY"),
    "perplexity": os.getenv("PERPLEXITY_KEY"),
    "deepseek": os.getenv("DEEPSEEK_KEY"),
    "claude": os.getenv("CLAUDE_KEY")
}

# API endpoints
API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "perplexity": "https://api.perplexity.ai/chat/completions",
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "claude": "https://api.anthropic.com/v1/messages"
}

# Provider priority (updated order)
PROVIDER_PRIORITY = ["openai", "groq", "perplexity", "deepseek", "claude"]

# Track provider status
provider_status = {provider: True for provider in PROVIDER_PRIORITY}

# Predefined responses for specific commands
PREDEFINED_RESPONSES = {
    "/study": "I'd be happy to help you with your studies! What subject are you working on right now?",
    "/plan": "Let's create a study plan together. What's your upcoming test or project about?",
    "/motivate": "Remember that every expert was once a beginner. You're capable of amazing things when you put your mind to it! What specific challenge are you facing?",
    "/help": "I'm here to help you with your studies! You can ask me about any subject, request study tips, create a study plan, or just chat.",
    "/hello": "Hello there! I'm SKY Dost, your AI study friend. How can I assist you with your studies today?",
    "/math": "I'd be happy to help with math! Are you working on algebra, calculus, or geometry?",
    "/science": "Science is fascinating! What specific topic are you studying? Physics, Chemistry, or Biology?",
    "/english": "I can help with English literature, grammar, or writing. What do you need help with?",
    "/history": "History teaches us about our past. What period or event are you studying?",
    "/physics": "Physics explains how our universe works! Are you studying mechanics, electricity, or thermodynamics?",
    "/chemistry": "Chemistry is the study of matter and its transformations. What topic are you working on?",
    "/biology": "Biology explores living organisms and their processes. What area are you studying?",
}

# Comprehensive fallback responses
SUBJECT_RESPONSES = {
    "math": [
        "Mathematics helps develop logical thinking! Are you working on algebra, geometry, calculus, or statistics?",
        "I'd be happy to help with math concepts. What specific problem or topic are you studying?",
        "Math can be challenging but rewarding! Let me know what you're working on."
    ],
    "science": [
        "Science helps us understand the natural world! Are you studying physics, chemistry, biology, or earth science?",
        "I can help with various scientific concepts. What specific area are you exploring?",
        "Science is all about curiosity and discovery! What would you like to learn about?"
    ],
    "physics": [
        "Physics explains how our universe works! Are you studying mechanics, electricity, thermodynamics, or waves?",
        "I can help with physics concepts. What specific topic or problem are you working on?",
        "Physics can be fascinating! Let me know what you're studying."
    ],
    "chemistry": [
        "Chemistry is the study of matter and its transformations! Are you working on elements, compounds, reactions, or equations?",
        "I can help with chemistry concepts. What specific area are you studying?",
        "Chemistry helps us understand the building blocks of our world! What topic interests you?"
    ],
    "biology": [
        "Biology explores living organisms and life processes! Are you studying cells, genetics, evolution, or ecology?",
        "I can help with biological concepts. What specific topic are you working on?",
        "Biology helps us understand life itself! What would you like to learn about?"
    ],
    "english": [
        "English language and literature open doors to communication and culture! Are you working on grammar, writing, reading, or analysis?",
        "I can help with English studies. What specific area do you need assistance with?",
        "English skills are essential for effective communication! What are you working on?"
    ],
    "history": [
        "History helps us understand our past and present! Are you studying ancient, medieval, modern, or world history?",
        "I can provide historical context and information. What specific period or event interests you?",
        "History lessons teach us about human experiences! What would you like to explore?"
    ],
    "study": [
        "Effective studying requires good habits! Try breaking material into smaller chunks and reviewing regularly.",
        "A good study technique is the Pomodoro method: 25 minutes of focused study followed by a 5-minute break.",
        "Remember to create a dedicated study space free from distractions for better concentration."
    ],
    "plan": [
        "Let's create a study plan! First, identify what you need to study and how much time you have available.",
        "A good study plan includes specific goals, scheduled study times, and regular review sessions.",
        "When creating a study plan, be realistic about your time and include breaks to avoid burnout."
    ],
    "motivate": [
        "Remember that every expert was once a beginner. Keep going and don't give up!",
        "Learning is a journey, not a destination. Celebrate your progress along the way!",
        "You're capable of amazing things when you put your mind to it. Believe in yourself!"
    ]
}

# Default responses for general queries
DEFAULT_RESPONSES = [
    "I'd be happy to help with your studies! What specific subject are you working on?",
    "Let's focus on your education. What would you like to learn about today?",
    "I'm here to assist with your learning journey. What topic are you studying?",
    "Education is the key to success. What would you like to explore today?",
    "I can help you with various subjects. What are you working on right now?",
    "Learning is a wonderful adventure! What subject would you like to discuss?",
    "I'm ready to help with your studies. What would you like to focus on today?"
]

# Greeting responses
GREETING_RESPONSES = [
    "Hello! I'm SKY Dost, your study assistant. How can I help with your studies today?",
    "Hi there! I'm here to help you learn. What subject are you working on?",
    "Greetings! I'm SKY Dost, ready to assist with your educational journey.",
    "Welcome! I'm your study companion. What would you like to learn about today?",
    "Hey there! Ready to explore some knowledge together? What are you studying?"
]

# Mode-specific prompts
MODE_PROMPTS = {
    "general": "You are SKY Dost, a friendly and helpful AI study assistant. Provide helpful, educational responses to the user's questions about their studies.",
    "subject": "You are SKY Dost, an expert tutor. Provide detailed explanations about academic subjects, break down complex concepts, and offer learning strategies.",
    "informative": "You are SKY Dost, an informative research assistant. Provide comprehensive, well-structured information with examples and practical applications.",
    "motivation": "You are SKY Dost, a motivational coach. Provide encouraging, uplifting responses that help students stay focused and overcome challenges."
}

def call_ai_provider(provider, user_message, mode="general"):
    """Call specific AI provider API with mode context"""
    headers = {
        "Content-Type": "application/json",
    }
    
    # Add appropriate API key
    if provider == "openai":
        if not API_KEYS["openai"] or API_KEYS["openai"] in ["", "your-openai-api-key-here"]:
            return None
            
        headers["Authorization"] = f"Bearer {API_KEYS['openai']}"
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": MODE_PROMPTS.get(mode, MODE_PROMPTS["general"])},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
    elif provider == "groq":
        if not API_KEYS["groq"] or API_KEYS["groq"] in ["", "your-groq-api-key-here"]:
            return None
            
        headers["Authorization"] = f"Bearer {API_KEYS['groq']}"
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": MODE_PROMPTS.get(mode, MODE_PROMPTS["general"])},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 512
        }
    elif provider == "perplexity":
        if not API_KEYS["perplexity"] or API_KEYS["perplexity"] in ["", "your-perplexity-api-key-here"]:
            return None
            
        headers["Authorization"] = f"Bearer {API_KEYS['perplexity']}"
        data = {
            "model": "sonar-small-chat",
            "messages": [
                {"role": "system", "content": MODE_PROMPTS.get(mode, MODE_PROMPTS["general"])},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }
    elif provider == "deepseek":
        if not API_KEYS["deepseek"] or API_KEYS["deepseek"] in ["", "your-deepseek-api-key-here"]:
            return None
            
        headers["Authorization"] = f"Bearer {API_KEYS['deepseek']}"
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": MODE_PROMPTS.get(mode, MODE_PROMPTS["general"])},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
    elif provider == "claude":
        if not API_KEYS["claude"] or API_KEYS["claude"] in ["", "your-claude-api-key-here"]:
            return None
            
        headers["x-api-key"] = API_KEYS['claude']
        headers["anthropic-version"] = "2023-06-01"
        data = {
            "model": "claude-instant-1.2",
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": f"{MODE_PROMPTS.get(mode, MODE_PROMPTS['general'])}\n\n{user_message}"}
            ]
        }
    else:
        return None
    
    try:
        response = requests.post(API_ENDPOINTS[provider], headers=headers, json=data, timeout=30, verify=True)
        
        # Check for specific error conditions
        if response.status_code == 401:  # Unauthorized
            print(f"⚠️ {provider}: Invalid API key")
            provider_status[provider] = False
            return None
        elif response.status_code == 402:  # Payment required
            print(f"⚠️ {provider}: Payment required")
            provider_status[provider] = False
            return None
        elif response.status_code == 429:  # Rate limited
            print(f"⚠️ {provider}: Rate limited")
            # Don't disable completely, just skip for now
            return None
        elif response.status_code == 400:  # Bad request
            print(f"⚠️ {provider}: Bad request - {response.text}")
            # Try with different parameters next time
            return None
            
        response.raise_for_status()
        result = response.json()
        
        # Extract response based on provider
        if provider == "claude":
            return result["content"][0]["text"]
        elif provider in ["openai", "deepseek", "groq"]:
            return result["choices"][0]["message"]["content"]
        elif provider == "perplexity":
            return result["choices"][0]["message"]["content"]
        else:
            return None
    except Exception as e:
        print(f"Error calling {provider}: {str(e)}")
        # Don't disable provider on network errors, only on auth/payment errors
        if "401" in str(e) or "402" in str(e) or "quota" in str(e).lower():
            provider_status[provider] = False
        return None

def get_ai_response(user_message, mode="general"):
    """Get response from AI providers with fallback mechanism"""
    # Try each provider in priority order
    for provider in PROVIDER_PRIORITY:
        # Skip if provider is disabled or no API key
        if not provider_status.get(provider, True):
            continue
            
        if API_KEYS.get(provider) and API_KEYS[provider] not in [None, "", "your-api-key-here"]:
            print(f"Trying {provider}...")
            response = call_ai_provider(provider, user_message, mode)
            if response:
                print(f"✅ Success with {provider}")
                return response, provider
    
    # If all AI providers fail, use fallback
    print("All AI providers failed, using fallback")
    return get_fallback_response(user_message), "fallback"

def get_fallback_response(user_message):
    """Generate an appropriate fallback response based on the user's message"""
    message_lower = user_message.lower()
    
    # Check for predefined commands
    if message_lower in PREDEFINED_RESPONSES:
        return PREDEFINED_RESPONSES[message_lower]
    
    # Check for greetings
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return random.choice(GREETING_RESPONSES)
    
    # Check for subject keywords
    for subject, responses in SUBJECT_RESPONSES.items():
        if subject in message_lower:
            return random.choice(responses)
    
    # Check for study-related keywords
    study_keywords = ["learn", "study", "teach", "education", "school", "college", "class"]
    if any(keyword in message_lower for keyword in study_keywords):
        return random.choice(DEFAULT_RESPONSES)
    
    # Return a random default response for other queries
    return random.choice(DEFAULT_RESPONSES)

@app.route("/")
def index():
    # Initialize chat history if it doesn't exist
    if "chat_history" not in session:
        session["chat_history"] = []
    if "current_mode" not in session:
        session["current_mode"] = "general"
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    mode = request.json.get("mode", session.get("current_mode", "general"))
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Update current mode in session
    session["current_mode"] = mode

    # Check for predefined commands first
    if user_message.lower() in PREDEFINED_RESPONSES:
        response_text = PREDEFINED_RESPONSES[user_message.lower()]
    else:
        # Use AI providers with fallback
        response_text, provider = get_ai_response(user_message, mode)
        # We're not sending provider info to frontend anymore

    # Update chat history in session
    chat_history = session.get("chat_history", [])
    chat_history.append({
        "user": user_message, 
        "bot": response_text, 
        "timestamp": time.time(),
        "mode": mode
    })
    session["chat_history"] = chat_history
    
    # Return only the answer without provider info
    return jsonify({"answer": response_text})

@app.route("/mode", methods=["POST"])
def set_mode():
    """Set the current conversation mode"""
    mode = request.json.get("mode", "general")
    session["current_mode"] = mode
    return jsonify({"status": "success", "mode": mode})

@app.route("/clear", methods=["POST"])
def clear_chat():
    """Clear the chat history"""
    session["chat_history"] = []
    # Reset provider status on clear
    for provider in PROVIDER_PRIORITY:
        provider_status[provider] = True
    return jsonify({"status": "success"})

@app.route("/status", methods=["GET"])
def status_check():
    """Check API status for all providers"""
    status = {}
    for provider in PROVIDER_PRIORITY:
        status[provider] = {
            "available": bool(API_KEYS.get(provider) and API_KEYS[provider] not in [None, "", "your-api-key-here"]),
            "key_configured": bool(API_KEYS.get(provider) and API_KEYS[provider] not in [None, "", "your-api-key-here"]),
            "enabled": provider_status.get(provider, True)
        }
    
    # Check if any provider is available
    any_available = any(
        status[provider]["available"] and status[provider]["enabled"] 
        for provider in PROVIDER_PRIORITY
    )
    status["any_provider_available"] = any_available
    status["mode"] = "AI Assistant Ready" if any_available else "Basic Mode"
    
    return jsonify(status)

if __name__ == "__main__":
    print("=" * 50)
    print("SKY Dost - Your AI Study Friend")
    print("=" * 50)
    
    # Check which providers are available
    available_providers = []
    for provider in PROVIDER_PRIORITY:
        if API_KEYS.get(provider) and API_KEYS[provider] not in [None, "", "your-api-key-here"]:
            available_providers.append(provider)
    
    if available_providers:
        print("✅ AI Providers Available:", ", ".join(available_providers))
        print("🔀 Fallback Priority:", " → ".join(PROVIDER_PRIORITY))
        print("💡 Tip: Make sure your API keys are valid and have sufficient credits")
    else:
        print("✅ Mode: Fallback System (Always Available)")
        print("💡 Tip: Add API keys to .env file to enable AI providers")
    
    print("🌐 Server running on http://127.0.0.1:5000")
    print("=" * 50)
    
    app.run(debug=True)