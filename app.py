import streamlit as st
import random
import time
import os
import json
import uuid
import threading
import redis
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Retro Chat",
    page_icon="🕹️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "transition_effect" not in st.session_state:
    st.session_state.transition_effect = True
if "new_messages" not in st.session_state:
    st.session_state.new_messages = []
if "new_requests" not in st.session_state:
    st.session_state.new_requests = []

# Redis Configuration
# Key prefixes for different data types
CHATROOM_PREFIX = "chatroom:"
MESSAGE_PREFIX = "message:"
REQUEST_PREFIX = "request:"

# Chatroom expiration time (24 hours)
CHATROOM_EXPIRY = 60 * 60 * 24

# Redis client singleton
@st.cache_resource
def get_redis_client():
    """Initialize and return Redis client"""
    # Try to get from environment variables
    redis_url = os.getenv("REDIS_URL")
    redis_password = os.getenv("REDIS_PASSWORD")
    
    # If not found, try to get from Streamlit secrets
    if not redis_url:
        try:
            redis_url = st.secrets["REDIS_URL"]
            redis_password = st.secrets.get("REDIS_PASSWORD", None)
        except:
            # Default to localhost for development
            redis_url = "redis://localhost:6379"
            redis_password = None
    
    # Connect to Redis
    if redis_password:
        client = redis.from_url(redis_url, password=redis_password)
    else:
        client = redis.from_url(redis_url)
    
    return client

# Enhanced styling with inline CSS - no external files needed
st.markdown("""
<style>
/* Base Styling */
body {
    background-color: #120458;
    background-image: linear-gradient(180deg, #120458 0%, #000000 100%);
    color: #fff;
    font-family: monospace;
}

/* CRT Screen Effect */
body::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
    background-size: 100% 2px, 3px 100%;
    pointer-events: none;
    z-index: 999;
}

/* Random Glitch Effect */
@keyframes random-glitch {
    0%, 100% { 
        clip-path: inset(80% 0 0 0);
        transform: translate(-2px, 0);
    }
    20% { 
        clip-path: inset(10% 0 60% 0); 
        transform: translate(2px, 0);
    }
    40% { 
        clip-path: inset(30% 0 20% 0); 
        transform: translate(0, 2px);
    }
    60% { 
        clip-path: inset(10% 0 70% 0); 
        transform: translate(-2px, -2px);
    }
    80% { 
        clip-path: inset(50% 0 30% 0); 
        transform: translate(2px, -2px);
    }
}

/* Scanline Effect */
@keyframes scanline {
    0% {
        transform: translateY(-100%);
    }
    100% {
        transform: translateY(100%);
    }
}

.scanline {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 5px;
    background: rgba(255, 255, 255, 0.1);
    z-index: 998;
    opacity: 0.3;
    animation: scanline 8s linear infinite;
}

/* VHS Tracking Lines */
@keyframes tracking {
    0% {
        transform: translateY(-100%);
    }
    100% {
        transform: translateY(200%);
    }
}

.tracking-line {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 15px;
    background: rgba(0, 255, 249, 0.03);
    z-index: 997;
    animation: tracking 15s linear infinite;
}

/* Power On Animation */
@keyframes power-on {
    0% {
        opacity: 0;
        transform: scale(0.8);
        filter: brightness(0);
    }
    10% {
        opacity: 0.5;
        transform: scale(0.9);
        filter: brightness(0.5) blur(10px);
    }
    30% {
        opacity: 0.8;
        filter: brightness(1.2) blur(5px);
    }
    40% {
        filter: brightness(0.8) blur(0);
    }
    50% {
        filter: brightness(1.2);
    }
    60% {
        filter: brightness(0.9);
    }
    70% {
        filter: brightness(1.1);
    }
    80%, 100% {
        opacity: 1;
        transform: scale(1);
        filter: brightness(1);
    }
}

.power-on {
    animation: power-on 2s forwards;
}

/* Page Transition Effect */
@keyframes crt-off {
    0% {
        opacity: 1;
        transform: scale(1);
        filter: brightness(1);
    }
    10% {
        filter: brightness(1.5);
    }
    30% {
        transform: scale(1.02, 0.8);
        filter: brightness(10);
    }
    40% {
        transform: scale(1, 0.1);
        filter: brightness(10);
    }
    50%, 100% {
        transform: scale(0, 0.1);
        filter: brightness(0);
        opacity: 0;
    }
}

@keyframes crt-on {
    0% {
        opacity: 0;
        transform: scale(1, 0.01);
        filter: brightness(0);
    }
    10% {
        opacity: 1;
        transform: scale(1, 0.03);
        filter: brightness(5);
    }
    30% {
        transform: scale(1.02, 0.5);
        filter: brightness(2);
    }
    50% {
        transform: scale(1.02, 1.02);
        filter: brightness(1.5);
    }
    70% {
        transform: scale(0.99, 0.99);
    }
    100% {
        transform: scale(1);
        filter: brightness(1);
    }
}

.crt-off {
    animation: crt-off 0.8s forwards;
}

.crt-on {
    animation: crt-on 1s forwards;
}

/* Neon Text */
.neon-text {
    color: #fff;
    text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #0073e6, 0 0 20px #0073e6, 0 0 25px #0073e6, 0 0 30px #0073e6, 0 0 35px #0073e6;
}

.hot-pink-text {
    color: #ff00c1;
    text-shadow: 0 0 5px #ff00c1, 0 0 10px #ff00c1, 0 0 15px #ff00c1, 0 0 20px #ff00c1;
}

.cyan-text {
    color: #00fff9;
    text-shadow: 0 0 5px #00fff9, 0 0 10px #00fff9, 0 0 15px #00fff9, 0 0 20px #00fff9;
}

.lime-text {
    color: #adff2f;
    text-shadow: 0 0 5px #adff2f, 0 0 10px #adff2f, 0 0 15px #adff2f, 0 0 20px #adff2f;
}

/* Pulsing Neon */
@keyframes neon-pulse {
    0%, 100% {
        text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #0073e6, 0 0 20px #0073e6, 0 0 25px #0073e6;
    }
    50% {
        text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #0073e6, 0 0 20px #0073e6, 0 0 25px #0073e6, 0 0 30px #0073e6, 0 0 35px #0073e6, 0 0 40px #0073e6;
    }
}

@keyframes pink-pulse {
    0%, 100% {
        text-shadow: 0 0 5px #ff00c1, 0 0 10px #ff00c1;
    }
    50% {
        text-shadow: 0 0 10px #ff00c1, 0 0 20px #ff00c1, 0 0 30px #ff00c1;
    }
}

@keyframes cyan-pulse {
    0%, 100% {
        text-shadow: 0 0 5px #00fff9, 0 0 10px #00fff9;
    }
    50% {
        text-shadow: 0 0 10px #00fff9, 0 0 20px #00fff9, 0 0 30px #00fff9;
    }
}

@keyframes lime-pulse {
    0%, 100% {
        text-shadow: 0 0 5px #adff2f, 0 0 10px #adff2f;
    }
    50% {
        text-shadow: 0 0 10px #adff2f, 0 0 20px #adff2f, 0 0 30px #adff2f;
    }
}

.neon-pulse {
    animation: neon-pulse 2s infinite;
}

.pink-pulse {
    animation: pink-pulse 2s infinite;
}

.cyan-pulse {
    animation: cyan-pulse 1.5s infinite;
}

.lime-pulse {
    animation: lime-pulse 2.5s infinite;
}

/* Retro Header */
h1 {
    font-size: 3rem;
    background: linear-gradient(90deg, #ff00c1, #00fff9, #adff2f);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 0.75rem #ff00c1);
    margin: 1rem 0;
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 2px;
}

@keyframes rainbow-shift {
    0% {
        background-position: 0% 50%;
    }
    50% {
        background-position: 100% 50%;
    }
    100% {
        background-position: 0% 50%;
    }
}

.rainbow-text {
    background: linear-gradient(90deg, #ff00c1, #00fff9, #adff2f, #ff00c1);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rainbow-shift 4s ease infinite;
}

h2 {
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: center;
}

/* Flicker Text Animation */
@keyframes text-flicker {
    0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% {
        opacity: 1;
    }
    20%, 21.999%, 63%, 63.999%, 65%, 69.999% {
        opacity: 0.4;
    }
}

.text-flicker {
    animation: text-flicker 4s linear infinite;
}

/* Glitch Text Animation */
@keyframes glitch-text {
    0%, 100% { 
        text-shadow: -2px 0 #ff00c1, 2px 0 #00fff9;
        transform: translate(0);
    }
    25% {
        text-shadow: -2px 0 #00fff9, 2px 0 #ff00c1;
        transform: translate(1px, 1px);
    }
    50% {
        text-shadow: 2px 0 #ff00c1, -2px 0 #adff2f;
        transform: translate(-1px, -1px);
    }
    75% {
        text-shadow: 2px 0 #adff2f, -2px 0 #00fff9;
        transform: translate(1px, -1px);
    }
}

.glitch-text {
    animation: glitch-text 3s infinite;
}

/* Button Styles */
.stButton button {
    background: black !important;
    color: #00fff9 !important;
    border: 3px solid #00fff9 !important;
    border-radius: 0 !important;
    box-shadow: 0 0 5px #00fff9, 0 0 10px #00fff9 !important;
    padding: 10px 24px !important;
    transition: all 0.3s !important;
    text-transform: uppercase !important;
    margin: 10px 0 !important;
    position: relative;
    overflow: hidden;
}

.stButton button:hover {
    background: #00fff9 !important;
    color: black !important;
    box-shadow: 0 0 10px #00fff9, 0 0 20px #00fff9, 0 0 30px #00fff9 !important;
    transform: scale(1.05) !important;
}

/* Button Hover Effect */
.stButton button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 255, 249, 0.4), transparent);
    transition: 0.5s;
    pointer-events: none;
}

.stButton button:hover::before {
    left: 100%;
}

/* Input Fields */
div[data-baseweb="input"] {
    background: #000 !important;
    border: 2px solid #ff00c1 !important;
    box-shadow: 0 0 5px #ff00c1 !important;
    transition: all 0.3s ease;
}

div[data-baseweb="input"]:focus-within {
    border: 2px solid #ff00c1 !important;
    box-shadow: 0 0 10px #ff00c1, 0 0 20px #ff00c1 !important;
}

input[type="text"] {
    color: #adff2f !important;
    font-size: 18px !important;
}

/* Room Code Display */
.room-code {
    letter-spacing: 5px;
    font-size: 2rem;
    color: #adff2f;
    text-shadow: 0 0 5px #adff2f, 0 0 10px #adff2f;
    background-color: rgba(0, 0, 0, 0.8);
    padding: 15px;
    border: 3px solid #adff2f;
    text-align: center;
    margin: 20px 0;
    position: relative;
    overflow: hidden;
}

@keyframes glow {
    0%, 100% {
        box-shadow: 0 0 5px #adff2f, 0 0 10px #adff2f;
    }
    50% {
        box-shadow: 0 0 10px #adff2f, 0 0 20px #adff2f, 0 0 30px #adff2f;
    }
}

.room-code {
    animation: glow 2s infinite;
}

/* Overlay for scan lines in containers */
.container-scan {
    position: relative;
}

.container-scan::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%);
    background-size: 100% 4px;
    pointer-events: none;
    z-index: 1;
}

/* Blinking cursor */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.blinking-cursor::after {
    content: "_";
    animation: blink 1s infinite;
}

/* Loading animation */
@keyframes loading {
    0% { content: ""; }
    25% { content: "."; }
    50% { content: ".."; }
    75% { content: "..."; }
    100% { content: "...."; }
}

.loading::after {
    content: "";
    animation: loading 1s infinite;
    display: inline-block;
    width: 20px;
    text-align: left;
}

/* Random Static Flash */
@keyframes static-flash {
    0%, 100% { opacity: 0; }
    5%, 10% { opacity: 0.1; }
    7% { opacity: 0.3; }
}

.static-flash {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAUVBMVEWFhYWDg4N3d3dtbW17e3t1dXWBgYGHh4d5eXlzc3OLi4ubm5uVlZWPj4+NjY19fX2JiYl/f39ra2uRkZGZmZlpaWmXl5dvb29xcXGTk5NnZ2c8TV1mAAAAG3RSTlNAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEAvEOwtAAAFVklEQVR4XpWWB67c2BUFb3g557T/hRo9/WUMZHlgr4Bg8Z4qQgQJlHI4A8SzFVrapvmTF9O7dmYRFZ60YiBhJRCgh1FYhiLAmdvX0CzTOpNE77ME0Zty/nWWzchDtiqrmQDeuv3powQ5ta2eN0FY0InkqDD73lT9c9lEzwUNqgFHs9VQce3TVClFCQrSTfOiYkVJQBmpbq2L6iZavPnAPcoU0dSw0SUTqz/GtrGuXfbyyBniKykOWQWGqwwMA7QiYAxi+IlPdqo+hYHnUt5ZPfnsHJyNiDtnpJyayNBkF6cWoYGAMY92U2hXHF/C1M8uP/ZtYdiuj26UdAdQQSXQErwSOMzt/XWRWAz5GuSBIkwG1H3FabJ2OsUOUhGC6tK4EMtJO0ttC6IBD3kM0ve0tJwMdSfjZo+EEISaeTr9P3wYrGjXqyC1krcKdhMpxEnt5JetoulscpyzhXN5FRpuPHvbeQaKxFAEB6EN+cYN6xD7RYGpXpNndMmZgM5Dcs3YSNFDHUo2LGfZuukSWyUYirJAdYbF3MfqEKmjM+I2EfhA94iG3L7uKrR+GdWD73ydlIB+6hgref1QTlmgmbM3/LeX5GI1Ux1RWpgxpLuZ2+I+IjzZ8wqE4nilvQdkUdfhzI5QDWy+kw5");
    pointer-events: none;
    z-index: 998;
    opacity: 0;
    animation: static-flash 8s linear infinite;
}

/* Footer */
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: rgba(0,0,0,0.7);
    padding: 5px;
    border-top: 2px solid #ff00c1;
    text-align: center;
    font-size: 14px;
    color: #adff2f;
}

/* Chat Container */
.chat-container {
    background-color: rgba(0, 0, 0, 0.7);
    border: 3px solid #ff00c1;
    border-radius: 0;
    box-shadow: 0 0 10px #ff00c1;
    padding: 20px;
    margin: 20px 0;
    height: 400px;
    overflow-y: auto;
    position: relative;
}

/* Message Styles */
.message {
    margin-bottom: 15px;
    padding: 10px;
    border-radius: 0;
    animation: typing 0.5s steps(40, end);
    position: relative;
}

.user-message {
    background-color: rgba(173, 255, 47, 0.2);
    border-left: 4px solid #adff2f;
    margin-left: 20px;
}

.other-message {
    background-color: rgba(0, 255, 249, 0.2);
    border-left: 4px solid #00fff9;
}

.system-message {
    background-color: rgba(255, 0, 193, 0.2);
    border-left: 4px solid #ff00c1;
    font-family: monospace;
    font-size: 0.9rem;
    text-align: center;
    animation: text-flicker 4s linear infinite;
}

/* Text typing animation */
@keyframes typing {
    from { width: 0 }
    to { width: 100% }
}

.typing-animation {
    overflow: hidden;
    white-space: nowrap;
    animation: typing 3s steps(40, end);
}

/* Background power lines effect */
.power-grid {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: 
        linear-gradient(90deg, rgba(173, 255, 47, 0.03) 1px, transparent 1px),
        linear-gradient(0deg, rgba(0, 255, 249, 0.03) 1px, transparent 1px);
    background-size: 20px 20px;
    pointer-events: none;
    z-index: -1;
}

@keyframes grid-movement {
    0% {
        background-position: 0 0;
    }
    100% {
        background-position: 20px 20px;
    }
}

.power-grid {
    animation: grid-movement 10s linear infinite;
}

/* Pending requests area */
.requests-container {
    background-color: rgba(0, 0, 0, 0.8);
    border: 2px solid #adff2f;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 10px #adff2f;
}

.request-item {
    background-color: rgba(255, 0, 193, 0.2);
    border-left: 3px solid #ff00c1;
    padding: 10px;
    margin-bottom: 10px;
}
</style>

<!-- Dynamic background effects -->
<div class="scanline"></div>
<div class="tracking-line" style="top: 30%;"></div>
<div class="tracking-line" style="top: 60%;"></div>
<div class="static-flash"></div>
<div class="power-grid"></div>

<script>
// Function to add CRT on/off effect when changing pages
function addPageTransitionEffects() {
    // Create container for our transition
    let container = document.createElement('div');
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.backgroundColor = 'black';
    container.style.zIndex = '9999';
    container.classList.add('crt-off');
    document.body.appendChild(container);

    // Remove after animation completes
    setTimeout(() => {
        document.body.removeChild(container);
    }, 800);
}

// Add random glitch effects occasionally
function randomGlitchEffect() {
    if (Math.random() < 0.05) {  // 5% chance per interval
        let glitchElement = document.createElement('div');
        glitchElement.style.position = 'fixed';
        glitchElement.style.top = '0';
        glitchElement.style.left = '0';
        glitchElement.style.width = '100%';
        glitchElement.style.height = '100%';
        glitchElement.style.backgroundColor = 'rgba(0, 255, 249, 0.1)';
        glitchElement.style.zIndex = '9998';
        glitchElement.style.animation = 'random-glitch 0.2s forwards';
        document.body.appendChild(glitchElement);

        setTimeout(() => {
            document.body.removeChild(glitchElement);
        }, 200);
    }
}

// Function to scroll chat to bottom
function scrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Add this for initial loading effect
window.addEventListener('load', function() {
    document.body.classList.add('power-on');
    
    // Set interval for random glitch effects
    setInterval(randomGlitchEffect, 2000);
    
    // Auto-scroll chat
    setInterval(scrollChatToBottom, 500);
});
</script>
""", unsafe_allow_html=True)

# Create footer
st.markdown(
    """
    <div class="footer">
        <span class="lime-pulse">RETRO-CHAT v1.0</span> | <span class="cyan-text">© 2025</span> | <span class="text-flicker">PRESS ESC TO EXIT</span>
    </div>
    """,
    unsafe_allow_html=True
)

# ----- Redis Database Operations -----

def create_chatroom(name, host_name):
    """Create a new chatroom and return its code and ID"""
    client = get_redis_client()
    
    # Generate a random 5-digit code
    code = str(random.randint(10000, 99999))
    
    # Generate a unique ID
    room_id = str(uuid.uuid4())
    
    # Create chatroom data
    chatroom_data = {
        "id": room_id,
        "name": name,
        "code": code,
        "host_name": host_name,
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    
    # Store in Redis with expiration
    key = f"{CHATROOM_PREFIX}{room_id}"
    client.set(key, json.dumps(chatroom_data))
    client.expire(key, CHATROOM_EXPIRY)
    
    # Also create a lookup by code
    client.set(f"{CHATROOM_PREFIX}code:{code}", room_id)
    client.expire(f"{CHATROOM_PREFIX}code:{code}", CHATROOM_EXPIRY)
    
    return {
        "success": True,
        "code": code,
        "id": room_id
    }

def get_chatroom_by_code(code):
    """Retrieve a chatroom by its code"""
    client = get_redis_client()
    
    # Get room ID from code
    room_id = client.get(f"{CHATROOM_PREFIX}code:{code}")
    
    if not room_id:
        return {
            "success": False,
            "error": "Chatroom not found or inactive"
        }
    
    room_id = room_id.decode('utf-8')
    
    # Get chatroom data
    chatroom_data = client.get(f"{CHATROOM_PREFIX}{room_id}")
    
    if not chatroom_data:
        return {
            "success": False,
            "error": "Chatroom not found or inactive"
        }
    
    chatroom = json.loads(chatroom_data)
    
    # Check if active
    if not chatroom.get("is_active", False):
        return {
            "success": False,
            "error": "Chatroom is inactive"
        }
    
    return {
        "success": True,
        "chatroom": chatroom
    }

def join_request(chatroom_id, username):
    """Create a join request for a user"""
    client = get_redis_client()
    
    # Generate a unique request ID
    request_id = str(uuid.uuid4())
    
    # Create request data
    request_data = {
        "id": request_id,
        "chatroom_id": chatroom_id,
        "username": username,
        "status": "pending",  # pending, approved, rejected
        "created_at": datetime.now().isoformat()
    }
    
    # Store in Redis with expiration (30 minutes)
    key = f"{REQUEST_PREFIX}{request_id}"
    client.set(key, json.dumps(request_data))
    client.expire(key, 60 * 30)  # 30 minutes expiry
    
    # Add to pending requests list for this chatroom
    client.sadd(f"{REQUEST_PREFIX}pending:{chatroom_id}", request_id)
    
    # Publish event for real-time updates
    client.publish(f"join-requests:{chatroom_id}", json.dumps({
        "type": "new_request",
        "request_id": request_id,
        "username": username
    }))
    
    return {
        "success": True,
        "request_id": request_id
    }

def get_pending_requests(chatroom_id):
    """Get all pending join requests for a chatroom"""
    client = get_redis_client()
    
    # Get all pending request IDs for this chatroom
    request_ids = client.smembers(f"{REQUEST_PREFIX}pending:{chatroom_id}")
    
    if not request_ids:
        return []
    
    # Get request data for each ID
    requests = []
    for req_id in request_ids:
        req_id = req_id.decode('utf-8')
        request_data = client.get(f"{REQUEST_PREFIX}{req_id}")
        if request_data:
            requests.append(json.loads(request_data))
    
    return requests

def update_request_status(request_id, status):
    """Update the status of a join request"""
    client = get_redis_client()
    
    # Get request data
    request_data = client.get(f"{REQUEST_PREFIX}{request_id}")
    
    if not request_data:
        return None
    
    request = json.loads(request_data)
    
    # Update status
    request["status"] = status
    client.set(f"{REQUEST_PREFIX}{request_id}", json.dumps(request))
    
    # If approved or rejected, remove from pending
    if status in ["approved", "rejected"]:
        client.srem(f"{REQUEST_PREFIX}pending:{request['chatroom_id']}", request_id)
    
    # Publish event for real-time updates
    client.publish(f"join-requests:{request['chatroom_id']}", json.dumps({
        "type": "status_update",
        "request_id": request_id,
        "username": request["username"],
        "status": status
    }))
    
    return request

def send_message(chatroom_id, username, content, message_type="user"):
    """Send a message to a chatroom"""
    client = get_redis_client()
    
    # Generate a unique message ID
    message_id = str(uuid.uuid4())
    
    # Create message data
    message_data = {
        "id": message_id,
        "chatroom_id": chatroom_id,
        "username": username,
        "content": content,
        "type": message_type,
        "created_at": datetime.now().isoformat()
    }
    
    # Store in Redis with expiration (same as chatroom)
    key = f"{MESSAGE_PREFIX}{message_id}"
    client.set(key, json.dumps(message_data))
    client.expire(key, CHATROOM_EXPIRY)
    
    # Add to messages list for this chatroom
    client.rpush(f"{MESSAGE_PREFIX}list:{chatroom_id}", message_id)
    
    # Publish event for real-time updates
    client.publish(f"messages:{chatroom_id}", json.dumps(message_data))
    
    return message_data

def get_messages(chatroom_id, limit=50):
    """Get messages for a chatroom"""
    client = get_redis_client()
    
    # Get the last 'limit' message IDs
    message_ids = client.lrange(f"{MESSAGE_PREFIX}list:{chatroom_id}", -limit, -1)
    
    if not message_ids:
        return []
    
    # Get message data for each ID
    messages = []
    for msg_id in message_ids:
        msg_id = msg_id.decode('utf-8')
        message_data = client.get(f"{MESSAGE_PREFIX}{msg_id}")
        if message_data:
            messages.append(json.loads(message_data))
    
    # Sort by created_at
    messages.sort(key=lambda x: x["created_at"])
    
    return messages

def close_chatroom(chatroom_id):
    """Mark a chatroom as inactive"""
    client = get_redis_client()
    
    # Get chatroom data
    chatroom_data = client.get(f"{CHATROOM_PREFIX}{chatroom_id}")
    
    if not chatroom_data:
        return None
    
    chatroom = json.loads(chatroom_data)
    
    # Update active status
    chatroom["is_active"] = False
    client.set(f"{CHATROOM_PREFIX}{chatroom_id}", json.dumps(chatroom))
    
    # Publish event for real-time updates
    client.publish(f"chatroom:{chatroom_id}", json.dumps({
        "type": "closed"
    }))
    
    return chatroom

# ----- Real-time Subscription Helpers -----

def start_message_listener(chatroom_id):
    """Start a thread to listen for new messages"""
    # Skip if already listening
    if hasattr(st.session_state, 'message_listener_started') and st.session_state.message_listener_started:
        return
    
    # Create a thread-safe callback
    def thread_safe_callback(message):
        try:
            data = json.loads(message["data"])
            st.session_state.new_messages.append(data)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    # Create and start thread
    def listen_for_messages():
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        pubsub = client.pubsub()
        
        # Subscribe to messages channel
        pubsub.subscribe(**{f"messages:{chatroom_id}": thread_safe_callback})
        
        # Listen for messages
        pubsub.run_in_thread(sleep_time=0.01)
    
    # Start thread
    thread = threading.Thread(target=listen_for_messages, daemon=True)
    thread.start()
    
    # Mark as started
    st.session_state.message_listener_started = True

def start_request_listener(chatroom_id):
    """Start a thread to listen for new join requests"""
    # Skip if already listening
    if hasattr(st.session_state, 'request_listener_started') and st.session_state.request_listener_started:
        return
    
    # Create a thread-safe callback
    def thread_safe_callback(message):
        try:
            data = json.loads(message["data"])
            st.session_state.new_requests.append(data)
        except Exception as e:
            print(f"Error processing request: {e}")
    
    # Create and start thread
    def listen_for_requests():
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        pubsub = client.pubsub()
        
        # Subscribe to join requests channel
        pubsub.subscribe(**{f"join-requests:{chatroom_id}": thread_safe_callback})
        
        # Listen for messages
        pubsub.run_in_thread(sleep_time=0.01)
    
    # Start thread
    thread = threading.Thread(target=listen_for_requests, daemon=True)
    thread.start()
    
    # Mark as started
    st.session_state.request_listener_started = True

def check_for_updates():
    """Process any updates from background threads"""
    # Check for new messages
    if st.session_state.new_messages:
        # Trigger a rerun to update the UI
        st.rerun()
    
    # Check for new join requests
    if st.session_state.new_requests:
        # Trigger a rerun to update the UI
        st.rerun()

# ----- Application Pages -----

def home_page():
    """Home page with options to host or join"""
    # Initialize Redis on app startup
    get_redis_client()
    
    # Title with enhanced animation
    st.markdown("<h1 class='rainbow-text'>RETRO CHAT</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style="text-align: center; color: #00fff9; font-size: 1.5rem; letter-spacing: 2px;" class="cyan-pulse">
            A BLAST FROM THE PAST
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    # Description with typing animation
    st.markdown(
        """
        <div style="text-align: center; margin: 30px 0;">
            <p style="font-size: 1.2rem; color: #adff2f;" class="typing-animation">
                Create or join a retro-styled temporary chatroom with your friends.
            </p>
            <p style="font-size: 1.2rem; color: #adff2f;" class="blinking-cursor">
                No accounts, no history, just pure nostalgic vibes
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Options
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="background-color: rgba(0, 0, 0, 0.7); border: 3px solid #ff00c1; padding: 30px; margin: 20px 0; box-shadow: 0 0 15px #ff00c1;" class="container-scan">
                <h2 style="color: #00fff9;" class="glitch-text">CHOOSE YOUR PATH</h2>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("HOST CHATROOM", key="host_btn"):
                # Add page transition effect
                if st.session_state.transition_effect:
                    st.markdown(
                        """
                        <script>
                        addPageTransitionEffects();
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                st.session_state.page = "host"
                st.rerun()
        
        with col_b:
            if st.button("JOIN CHATROOM", key="join_btn"):
                # Add page transition effect
                if st.session_state.transition_effect:
                    st.markdown(
                        """
                        <script>
                        addPageTransitionEffects();
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                st.session_state.page = "join"
                st.rerun()

def host_chatroom():
    """Host a new chatroom interface"""
    st.markdown("<h1 class='rainbow-text'>HOST A CHATROOM</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style="text-align: center; color: #00fff9; font-size: 1.2rem; letter-spacing: 1px;" class="cyan-pulse">
            Create your own retro chat space
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    # Input fields for chatroom name and host username - FIXED KEYS
    st.markdown('<p class="cyan-text text-flicker" style="margin-top: 30px;">ENTER CHATROOM INFO:</p>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            room_name = st.text_input("ROOM NAME", key="room_name_input", placeholder="MY RADICAL CHATROOM")
        with col2:
            host_name = st.text_input("YOUR NAME", key="host_name_input", placeholder="NEON_RIDER")
    
    # Create chatroom button
    if st.button("CREATE CHATROOM", key="create_room_btn"):
        if not room_name or not host_name:
            st.error("Please enter both room name and your name")
            return
        
        with st.spinner(""):
            # Show retro loading animation
            st.markdown(
                """
                <div style="text-align: center;">
                    <p class="hot-pink-text pink-pulse">INITIALIZING CHATROOM</p>
                    <div style="color: #00fff9;">
                        <span class="glitch-text loading">CONNECTING</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Create chatroom in Redis
            result = create_chatroom(room_name, host_name)
            
            # Add some delay for effect
            time.sleep(1.5)
            
            if result["success"]:
                # Store chatroom info in session state - FIXED KEYS
                st.session_state.room_code = result["code"]
                st.session_state.room_id = result["id"]
                st.session_state.username = host_name
                st.session_state.current_room_name = room_name  # Changed key here
                st.session_state.is_host = True
                st.session_state.page = "chat"
                
                # Add page transition effect
                if st.session_state.transition_effect:
                    st.markdown(
                        """
                        <script>
                        addPageTransitionEffects();
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.rerun()
            else:
                st.error(f"Error creating chatroom: {result.get('error', 'Unknown error')}")
    
    # Back button
    if st.button("BACK", key="back_btn"):
        # Add page transition effect
        if st.session_state.transition_effect:
            st.markdown(
                """
                <script>
                addPageTransitionEffects();
                </script>
                """,
                unsafe_allow_html=True
            )
        st.session_state.page = "home"
        st.rerun()

def join_chatroom():
    """Interface for joining an existing chatroom"""
    st.markdown("<h1 class='rainbow-text'>JOIN A CHATROOM</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style="text-align: center; color: #00fff9; font-size: 1.2rem; letter-spacing: 1px;" class="cyan-pulse">
            Enter the access code
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    # Input fields for room code and username - FIXED KEYS
    st.markdown('<p class="cyan-text text-flicker" style="margin-top: 30px;">ENTER ACCESS CREDENTIALS:</p>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            room_code = st.text_input("ROOM CODE", key="join_room_code_input", placeholder="12345")
        with col2:
            username = st.text_input("YOUR NAME", key="join_username_input", placeholder="PIXEL_PUNK")
    
    # Join button
    if st.button("JOIN CHATROOM", key="join_room_btn"):
        if not room_code or not username:
            st.error("Please enter both room code and your name")
            return
        
        # Show loading animation
        st.markdown(
            """
            <div style="text-align: center;">
                <p class="hot-pink-text pink-pulse">VALIDATING CODE</p>
                <div style="color: #00fff9;">
                    <span class="glitch-text loading">CONNECTING</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Get chatroom from Redis
        result = get_chatroom_by_code(room_code)
        
        # Add some delay for effect
        time.sleep(1.5)
        
        if result["success"]:
            chatroom = result["chatroom"]
            
            # Host approves automatically for this version
            # In a full version, you would wait for host approval
            
            # Store info in session state - FIXED KEYS
            st.session_state.room_code = room_code
            st.session_state.room_id = chatroom["id"]
            st.session_state.username = username
            st.session_state.current_room_name = chatroom["name"]  # Changed key here
            st.session_state.is_host = False
            st.session_state.page = "chat"
            
            # Send a system message about new user joining
            send_message(chatroom["id"], "SYSTEM", f"{username} has joined the chatroom", "system")
            
            # Add page transition effect
            if st.session_state.transition_effect:
                st.markdown(
                    """
                    <script>
                    addPageTransitionEffects();
                    </script>
                    """,
                    unsafe_allow_html=True
                )
            
            st.rerun()
        else:
            st.error(f"Error joining chatroom: {result.get('error', 'Invalid room code or room is inactive')}")
    
    # Back button
    if st.button("BACK", key="back_btn_join"):
        # Add page transition effect
        if st.session_state.transition_effect:
            st.markdown(
                """
                <script>
                addPageTransitionEffects();
                </script>
                """,
                unsafe_allow_html=True
            )
        st.session_state.page = "home"
        st.rerun()

def chat_interface():
    """Enhanced chat interface with Redis integration"""
    # Check if user is in a room
    if "room_id" not in st.session_state:
        st.session_state.page = "home"
        st.rerun()
        return
    
    # Start real-time listeners
    room_id = st.session_state.room_id
    start_message_listener(room_id)
    
    if st.session_state.get("is_host", False):
        start_request_listener(room_id)
    
    # Display chat header - FIXED KEY
    room_name = st.session_state.current_room_name  # Use current_room_name instead of room_name
    username = st.session_state.username
    is_host = st.session_state.get("is_host", False)
    
    header_suffix = " (HOST)" if is_host else ""
    st.markdown(f"<h1 class='rainbow-text'>CHATROOM: {room_name}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <p style="text-align: center; color: #00fff9; font-size: 1.2rem;" class="cyan-pulse">
            Logged in as: <span class="hot-pink-text">{username}{header_suffix}</span>
        </p>
        """, 
        unsafe_allow_html=True
    )
    
    # If host, display the room code for sharing
    if is_host:
        st.markdown(
            f"""
            <div class="room-code">{st.session_state.room_code}</div>
            <p class="lime-text lime-pulse" style="text-align: center;">SHARE THIS CODE WITH OTHERS TO JOIN</p>
            """, 
            unsafe_allow_html=True
        )
        
        # Handle join requests
        handle_join_requests()
    
    # Chat area and controls
    col1, col2 = st.columns([4, 1])
    
    # Side controls
    with col2:
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        if st.button("REFRESH", key="refresh_btn"):
            st.rerun()
        
        if st.button("EXIT CHATROOM", key="exit_btn"):
            exit_chat()
            
            # Add exit effect
            st.markdown(
                """
                <script>
                // More dramatic transition for exit
                let container = document.createElement('div');
                container.style.position = 'fixed';
                container.style.top = '0';
                container.style.left = '0';
                container.style.width = '100%';
                container.style.height = '100%';
                container.style.backgroundColor = 'black';
                container.style.zIndex = '9999';
                container.classList.add('crt-off');
                document.body.appendChild(container);
                </script>
                """,
                unsafe_allow_html=True
            )
            
            st.rerun()
        
        if is_host:
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            if st.button("CLOSE CHATROOM", key="close_btn"):
                close_chat()
                
                # Add exit effect 
                st.markdown(
                    """
                    <script>
                    // More dramatic transition for exit
                    let container = document.createElement('div');
                    container.style.position = 'fixed';
                    container.style.top = '0';
                    container.style.left = '0';
                    container.style.width = '100%';
                    container.style.height = '100%';
                    container.style.backgroundColor = 'black';
                    container.style.zIndex = '9999';
                    container.classList.add('crt-off');
                    document.body.appendChild(container);
                    </script>
                    """,
                    unsafe_allow_html=True
                )
                
                st.rerun()
    
    # Main chat area
    with col1:
        # Chat messages container
        st.markdown('<div class="chat-container container-scan" id="chat-container">', unsafe_allow_html=True)
        
        # Get messages from Redis
        messages = get_messages(room_id)
        
        # Initialize message count for notification
        if "message_count" not in st.session_state:
            st.session_state.message_count = 0
        
        # Check for new messages and update session state
        if len(messages) > st.session_state.message_count:
            st.session_state.message_count = len(messages)
        
        # Display messages with their appropriate styles
        if messages:
            for msg in messages:
                if msg["type"] == "system":
                    # System message
                    st.markdown(
                        f"""
                        <div class="message system-message">
                            {msg["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                elif msg["username"] == username:
                    # User's own message
                    st.markdown(
                        f"""
                        <div class="message user-message">
                            <span class="hot-pink-text">{msg["username"]}:</span> {msg["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Other users' messages
                    st.markdown(
                        f"""
                        <div class="message other-message">
                            <span class="cyan-text">{msg["username"]}:</span> {msg["content"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            # No messages yet
            st.markdown(
                """
                <div style="color: #adff2f; margin-top: 30px; text-align: center;" class="text-flicker">
                    NO MESSAGES YET
                </div>
                <div style="color: #00fff9; margin-top: 10px; text-align: center;">
                    Be the first to start the conversation!
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        message = st.text_input("", key="message_input", placeholder="TYPE YOUR MESSAGE HERE...")
        
        col_a, col_b = st.columns([5, 1])
        
        with col_b:
            if st.button("SEND", key="send_btn"):
                if message:
                    # Send message to Redis
                    send_message(room_id, username, message)
                    # Clear input 
                    st.session_state.message_input = ""
                    # Rerun to update chat
                    st.rerun()
                
        # Send on Enter key
        if message and message != st.session_state.get("last_message", ""):
            st.session_state.last_message = message
            # Send message to Redis
            send_message(room_id, username, message)
            # Clear input
            st.session_state.message_input = ""
            # Rerun to update chat
            st.rerun()
    
    # Check for updates from Redis pub/sub
    check_for_updates()

def handle_join_requests():
    """Display and handle join requests for host"""
    if not st.session_state.get("is_host", False):
        return
    
    # Get pending requests
    pending_requests = get_pending_requests(st.session_state.room_id)
    
    if pending_requests:
        st.markdown('<h3 class="lime-text lime-pulse">JOIN REQUESTS</h3>', unsafe_allow_html=True)
        
        # Initialize request count if not exists
        if "last_request_count" not in st.session_state:
            st.session_state.last_request_count = 0
        
        # Display each request with approve/reject buttons
        for request in pending_requests:
            with st.container():
                st.markdown(
                    f"""
                    <div class="request-item">
                        <span class="hot-pink-text">{request["username"]}</span> wants to join your chatroom
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("APPROVE", key=f"approve_{request['id']}"):
                        # Update request status in Redis
                        updated_request = update_request_status(request["id"], "approved")
                        if updated_request:
                            # Send system message
                            send_message(
                                st.session_state.room_id,
                                "SYSTEM",
                                f"{updated_request['username']} has joined the chatroom",
                                "system"
                            )
                            st.rerun()
                
                with col2:
                    if st.button("REJECT", key=f"reject_{request['id']}"):
                        # Update request status in Redis
                        update_request_status(request["id"], "rejected")
                        st.rerun()

def exit_chat():
    """Exit the current chatroom"""
    # Send exit message to Redis
    send_message(
        st.session_state.room_id,
        "SYSTEM",
        f"{st.session_state.username} has left the chatroom",
        "system"
    )
    
    # Clear chatroom data from session
    if "room_id" in st.session_state:
        del st.session_state.room_id
    if "current_room_name" in st.session_state:  # FIXED KEY
        del st.session_state.current_room_name
    if "room_code" in st.session_state:
        del st.session_state.room_code
    if "username" in st.session_state:
        del st.session_state.username
    if "is_host" in st.session_state:
        del st.session_state.is_host
    if "message_count" in st.session_state:
        del st.session_state.message_count
    if "message_listener_started" in st.session_state:
        del st.session_state.message_listener_started
    if "request_listener_started" in st.session_state:
        del st.session_state.request_listener_started
    
    # Go back to home
    st.session_state.page = "home"

def close_chat():
    """Close the chatroom (host only)"""
    if not st.session_state.get("is_host", False):
        return
    
    # Send closing message
    send_message(
        st.session_state.room_id,
        "SYSTEM",
        "The host has closed the chatroom",
        "system"
    )
    
    # Close chatroom in Redis
    close_chatroom(st.session_state.room_id)
    
    # Clear chatroom data from session
    if "room_id" in st.session_state:
        del st.session_state.room_id
    if "current_room_name" in st.session_state:  # FIXED KEY
        del st.session_state.current_room_name
    if "room_code" in st.session_state:
        del st.session_state.room_code
    if "username" in st.session_state:
        del st.session_state.username
    if "is_host" in st.session_state:
        del st.session_state.is_host
    if "message_count" in st.session_state:
        del st.session_state.message_count
    if "message_listener_started" in st.session_state:
        del st.session_state.message_listener_started
    if "request_listener_started" in st.session_state:
        del st.session_state.request_listener_started
    
    # Go back to home
    st.session_state.page = "home"

# Main application logic
def main():
    # Handle different pages
    if st.session_state.page == "home":
        home_page()
    elif st.session_state.page == "host":
        host_chatroom()
    elif st.session_state.page == "join":
        join_chatroom()
    elif st.session_state.page == "chat":
        chat_interface()

# Run the main application
if __name__ == "__main__":
    main()
