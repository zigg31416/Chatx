import streamlit as st
import base64
from pathlib import Path
import os
import time

def inject_custom_css():
    """Inject custom CSS"""
    # Get the directory of the current file
    current_dir = Path(__file__).parent.parent
    css_file = current_dir / "styles" / "style.css"
    
    # Check if the file exists
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {css_file}")

def local_css(file_name):
    """Load a local CSS file"""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_title(title, subtitle=None):
    """Display a retro-styled title and optional subtitle"""
    st.markdown(f'<h1 class="neon-text">{title}</h1>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<h3 class="cyan-text">{subtitle}</h3>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

def display_room_code(code):
    """Display the room code in a retro style"""
    st.markdown(f'<div class="room-code">{code}</div>', unsafe_allow_html=True)

def display_chat_message(username, content, message_type="user", current_username=None):
    """Display a chat message with appropriate styling"""
    if message_type == "system":
        # System message (join/leave notifications, etc.)
        if "left the chatroom" in content:
            st.markdown(f'<div class="message system-message exit-message">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message system-message">{content}</div>', unsafe_allow_html=True)
    else:
        # User message
        if current_username and username == current_username:
            # Current user's message
            st.markdown(
                f'<div class="message user-message">'
                f'<strong class="lime-text">{username}:</strong> {content}'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            # Other user's message
            st.markdown(
                f'<div class="message other-message">'
                f'<strong class="hot-pink-text">{username}:</strong> {content}'
                f'</div>',
                unsafe_allow_html=True
            )

def display_join_request(username, request_id, approve_callback, reject_callback):
    """Display a join request with approve/reject buttons"""
    with st.container():
        st.markdown(
            f'<div class="modal">'
            f'<h3 class="cyan-text">JOIN REQUEST</h3>'
            f'<p><strong class="hot-pink-text">{username}</strong> wants to join your chatroom</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("ACCEPT", key=f"accept_{request_id}"):
                approve_callback(request_id)
        with col2:
            if st.button("REJECT", key=f"reject_{request_id}"):
                reject_callback(request_id)

def add_glitch_effect():
    """Add a subtle VHS glitch effect overlay"""
    glitch_css = """
        <style>
        .glitch-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            opacity: 0.05;
        }
        .glitch-container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                repeating-linear-gradient(
                    0deg,
                    rgba(0, 0, 0, 0.15),
                    rgba(0, 0, 0, 0.15) 1px,
                    transparent 1px,
                    transparent 2px
                );
        }
        @keyframes noise {
            0%, 3%, 5%, 42%, 44%, 100% { opacity: 0; }
            4%, 43% { opacity: 1; }
        }
        @keyframes scan {
            0% { top: -100%; }
            100% { top: 100%; }
        }
        .scan-line {
            position: absolute;
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.08);
            animation: scan 6s linear infinite;
        }
        .noise {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAUVBMVEWFhYWDg4N3d3dtbW17e3t1dXWBgYGHh4d5eXlzc3OLi4ubm5uVlZWPj4+NjY19fX2JiYl/f39ra2uRkZGZmZlpaWmXl5dvb29xcXGTk5NnZ2c8TV1mAAAAG3RSTlNAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEAvEOwtAAAFVklEQVR4XpWWB67c2BUFb3g557T/hRo9/WUMZHlgr4Bg8Z4qQgQJlHI4A8SzFVrapvmTF9O7dmYRFZ60YiBhJRCgh1FYhiLAmdvX0CzTOpNE77ME0Zty/nWWzchDtiqrmQDeuv3powQ5ta2eN0FY0InkqDD73lT9c9lEzwUNqgFHs9VQce3TVClFCQrSTfOiYkVJQBmpbq2L6iZavPnAPcoU0dSw0SUTqz/GtrGuXfbyyBniKykOWQWGqwwMA7QiYAxi+IlPdqo+hYHnUt5ZPfnsHJyNiDtnpJyayNBkF6cWoYGAMY92U2hXHF/C1M8uP/ZtYdiuj26UdAdQQSXQErwSOMzt/XWRWAz5GuSBIkwG1H3FabJ2OsUOUhGC6tK4EMtJO0ttC6IBD3kM0ve0tJwMdSfjZo+EEISaeTr9P3wYrGjXqyC1krcKdhMpxEnt5JetoulscpyzhXN5FRpuPHvbeQaKxFAEB6EN+cYN6xD7RYGpXpNndMmZgM5Dcs3YSNFDHUo2LGfZuukSWyUYirJAdYbF3MfqEKmjM+I2EfhA94iG3L7uKrR+GdWD73ydlIB+6hgref1QTlmgmbM3/LeX5GI1Ux1RWpgxpLuZ2+I+IjzZ8wqE4nilvQdkUdfhzI5QDWy+kw5");
            animation: noise 0.2s infinite;
            opacity: 0.02;
        }
        </style>
        <div class="glitch-container">
            <div class="scan-line"></div>
            <div class="noise"></div>
        </div>
    """
    st.markdown(glitch_css, unsafe_allow_html=True)

def play_sound(sound_type="notification"):
    """Play a retro sound effect"""
    # Define base64 encoded sound data
    notification_sound = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAAABMYXZjNTguMTMuMTAw"
    
    # JavaScript to play the sound
    js = f"""
    <script>
    var audio = new Audio("{notification_sound}");
    audio.volume = 0.5;
    audio.play();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

def create_retro_animation():
    """Create a loading/transition animation"""
    animation = """
    <style>
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
    </style>
    <div style="font-family: 'Press Start 2P', cursive; font-size: 24px; color: #00fff9; text-shadow: 0 0 5px #00fff9, 0 0 10px #00fff9; margin: 20px 0;" class="loading">LOADING</div>
    """
    st.markdown(animation, unsafe_allow_html=True)
    time.sleep(1.5)  # Simulate loading

def create_retro_footer():
    """Create a retro-styled footer"""
    footer = """
    <div style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: rgba(0,0,0,0.7); padding: 5px; border-top: 2px solid #ff00c1; text-align: center; font-family: 'VT323', monospace; font-size: 14px; color: #adff2f;">
        RETRO-CHAT v1.0 | © 2025 | PRESS ESC TO EXIT
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)
