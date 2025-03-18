import streamlit as st
import time
from utils.redis_client import send_message, get_messages, close_chatroom
from utils.ui_elements import display_title, display_room_code, display_chat_message, play_sound
from utils.thread_manager import ThreadManager
from components.host import handle_join_requests

def chat_interface():
    """Main chat interface"""
    # Check if user is in a room
    if "room_id" not in st.session_state:
        st.session_state.page = "home"
        st.experimental_rerun()
        return
    
    # Display chat header
    room_name = st.session_state.room_name
    username = st.session_state.username
    is_host = st.session_state.get("is_host", False)
    
    header_suffix = " (HOST)" if is_host else ""
    display_title(f"CHATROOM: {room_name}", f"Logged in as: {username}{header_suffix}")
    
    # If host, display the room code for sharing
    if is_host:
        display_room_code(st.session_state.room_code)
        st.markdown('<p class="lime-text">SHARE THIS CODE WITH OTHERS TO JOIN</p>', unsafe_allow_html=True)
    
    # Handle join requests if host
    if is_host:
        handle_join_requests()
    
    # Layout chat area and input
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        if st.button("REFRESH", key="refresh_btn"):
            st.experimental_rerun()
        
        if st.button("EXIT CHATROOM", key="exit_btn"):
            exit_chat()
            st.experimental_rerun()
        
        if is_host:
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            if st.button("CLOSE CHATROOM", key="close_btn", help="This will end the chat for all users"):
                close_chat()
                st.experimental_rerun()
    
    with col1:
        # Chat messages container
        with st.container():
            st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
            
            # Get messages from Redis
            messages = get_messages(st.session_state.room_id)
            
            # Initialize message count for notification
            if "message_count" not in st.session_state:
                st.session_state.message_count = len(messages)
            
            # Display messages
            for msg in messages:
                display_chat_message(
                    msg["username"], 
                    msg["content"], 
                    msg["type"], 
                    st.session_state.username
                )
            
            # Check for new messages and play sound
            if len(messages) > st.session_state.message_count:
                play_sound("message")
            
            st.session_state.message_count = len(messages)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        message = st.text_input("", key="message_input", placeholder="TYPE YOUR MESSAGE HERE...")
        
        if message:
            # Send message to Redis
            send_message(st.session_state.room_id, st.session_state.username, message)
            
            # Clear input
            st.session_state.message_input = ""
            
            # Rerun to update chat
            st.experimental_rerun()
    
    # Set up real-time updates if not already started
    if 'message_listener_started' not in st.session_state:
        # Start thread to listen for new messages
        ThreadManager.start_message_listener(
            st.session_state.room_id,
            lambda data: None  # This is a placeholder, actual callback is in ThreadManager
        )
        st.session_state.message_listener_started = True
    
    # Check for updates from background threads
    ThreadManager.check_for_updates()
    
    # Add automatic scrolling
    st.markdown(
        """
        <script>
        function scrollToBottom() {
            const chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        
        // Call on load and set interval to check for new content
        window.addEventListener('load', scrollToBottom);
        setInterval(scrollToBottom, 500);
        </script>
        """,
        unsafe_allow_html=True
    )

def exit_chat():
    """Exit the current chatroom"""
    room_id = st.session_state.room_id
    username = st.session_state.username
    
    # Send exit message
    send_message(room_id, "SYSTEM", f"{username} has left the chatroom", "system")
    
    # Clear chatroom data from session
    if "room_id" in st.session_state:
        del st.session_state.room_id
    if "room_name" in st.session_state:
        del st.session_state.room_name
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
    
    # Go back to home
    st.session_state.page = "home"

def close_chat():
    """Close the chatroom (host only)"""
    if not st.session_state.get("is_host", False):
        return
    
    # Send closing message
    send_message(st.session_state.room_id, "SYSTEM", "The host has closed the chatroom", "system")
    
    # Close chatroom in Redis
    close_chatroom(st.session_state.room_id)
    
    # Clear chatroom data from session
    if "room_id" in st.session_state:
        del st.session_state.room_id
    if "room_name" in st.session_state:
        del st.session_state.room_name
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
    
    # Go back to home
    st.session_state.page = "home"