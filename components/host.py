import streamlit as st
import time
from utils.redis_client import create_chatroom, get_pending_requests, update_request_status
from utils.ui_elements import display_title, display_room_code, display_join_request, play_sound
from utils.thread_manager import ThreadManager

def host_chatroom():
    """Host a new chatroom interface"""
    display_title("HOST A CHATROOM", "Create your own retro chat space")
    
    # Check if already hosting
    if "is_host" in st.session_state and st.session_state.is_host:
        st.markdown('<p class="hot-pink-text">You are already hosting a chatroom</p>', unsafe_allow_html=True)
        if st.button("RETURN TO CHAT"):
            st.session_state.page = "chat"
            st.experimental_rerun()
        return
    
    # Input fields for chatroom name and host username
    st.markdown('<p class="cyan-text">ENTER CHATROOM INFO:</p>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            room_name = st.text_input("ROOM NAME", key="room_name", placeholder="MY RADICAL CHATROOM")
        with col2:
            host_name = st.text_input("YOUR NAME", key="host_name", placeholder="NEON_RIDER")
    
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
                    <p class="hot-pink-text">INITIALIZING CHATROOM</p>
                    <div style="font-family: 'Press Start 2P'; color: #00fff9;">
                        <span style="animation: glitch 1s infinite;">CONNECTING</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Create chatroom in Redis
            result = create_chatroom(room_name, host_name)
            time.sleep(1.5)  # Simulate loading
            
            if result["success"]:
                # Store chatroom info in session state
                st.session_state.room_code = result["code"]
                st.session_state.room_id = result["id"]
                st.session_state.username = host_name
                st.session_state.room_name = room_name
                st.session_state.is_host = True
                st.session_state.page = "chat"
                
                # Play creation sound (if implemented)
                play_sound("creation")
                
                st.experimental_rerun()
            else:
                st.error(f"Error creating chatroom: {result.get('error', 'Unknown error')}")

def handle_join_requests():
    """Component to display and handle join requests"""
    if not ("is_host" in st.session_state and st.session_state.is_host):
        return
    
    # Set up real-time updates if not already started
    if 'request_listener_started' not in st.session_state:
        # Start thread to listen for new join requests
        ThreadManager.start_request_listener(
            st.session_state.room_id,
            lambda data: None  # This is a placeholder, actual callback is in ThreadManager
        )
        st.session_state.request_listener_started = True
    
    # Get pending requests
    pending_requests = get_pending_requests(st.session_state.room_id)
    
    if pending_requests:
        st.markdown('<h3 class="lime-text">JOIN REQUESTS</h3>', unsafe_allow_html=True)
        
        # Play notification sound for new requests
        if "last_request_count" not in st.session_state:
            st.session_state.last_request_count = 0
            
        if len(pending_requests) > st.session_state.last_request_count:
            play_sound("notification")
            
        st.session_state.last_request_count = len(pending_requests)
        
        # Display each request with approve/reject buttons
        for request in pending_requests:
            display_join_request(
                request["username"],
                request["id"],
                lambda request_id=request["id"]: approve_request(request_id),
                lambda request_id=request["id"]: reject_request(request_id)
            )
    
    # Check for updates from background threads
    ThreadManager.check_for_updates()

def approve_request(request_id):
    """Approve a join request"""
    result = update_request_status(request_id, "approved")
    if result:
        st.success(f"User approved and can now join the chat")
        st.experimental_rerun()
    else:
        st.error("Failed to approve user")

def reject_request(request_id):
    """Reject a join request"""
    result = update_request_status(request_id, "rejected")
    if result:
        st.info("User rejected")
        st.experimental_rerun()
    else:
        st.error("Failed to reject user")