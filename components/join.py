import streamlit as st
import time
from utils.supabase_client import get_chatroom_by_code, join_request
from utils.ui_elements import display_title, create_retro_animation

def join_chatroom():
    """Interface for joining an existing chatroom"""
    display_title("JOIN A CHATROOM", "Enter the access code")
    
    # Check if already in a chatroom
    if "room_id" in st.session_state and not st.session_state.get("is_host", False):
        st.markdown('<p class="hot-pink-text">You are already in a chatroom</p>', unsafe_allow_html=True)
        if st.button("RETURN TO CHAT"):
            st.session_state.page = "chat"
            st.experimental_rerun()
        return
    
    # Input fields for room code and username
    st.markdown('<p class="cyan-text">ENTER ACCESS CREDENTIALS:</p>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            room_code = st.text_input("ROOM CODE", key="join_room_code", placeholder="12345")
        with col2:
            username = st.text_input("YOUR NAME", key="join_username", placeholder="PIXEL_PUNK")
    
    # Join button
    if st.button("JOIN CHATROOM", key="join_room_btn"):
        if not room_code or not username:
            st.error("Please enter both room code and your name")
            return
        
        # Show retro loading animation
        create_retro_animation()
        
        # Get chatroom info from Supabase
        result = get_chatroom_by_code(room_code)
        
        if result["success"]:
            chatroom = result["chatroom"]
            
            # Create join request
            request_result = join_request(chatroom["id"], username)
            
            if request_result["success"]:
                # Store request info in session state
                st.session_state.pending_request_id = request_result["request_id"]
                st.session_state.pending_room_id = chatroom["id"]
                st.session_state.pending_room_name = chatroom["name"]
                st.session_state.pending_username = username
                st.session_state.page = "waiting"
                
                st.experimental_rerun()
            else:
                st.error(f"Error joining chatroom: {request_result.get('error', 'Unknown error')}")
        else:
            st.error(f"Error: {result.get('error', 'Unknown error')}")

def waiting_room():
    """Waiting room for pending join requests"""
    if "pending_request_id" not in st.session_state:
        st.session_state.page = "join"
        st.experimental_rerun()
        return
    
    display_title("WAITING FOR APPROVAL", f"Room: {st.session_state.pending_room_name}")
    
    # Animated waiting message
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px;">
            <div style="font-family: 'Press Start 2P'; font-size: 20px; color: #00fff9; text-shadow: 0 0 5px #00fff9;">
                WAITING FOR HOST APPROVAL
            </div>
            <div style="margin-top: 30px; font-family: 'VT323'; font-size: 24px;">
                <span class="loading">STANDBY</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Check request status periodically
    if "check_timer" not in st.session_state:
        st.session_state.check_timer = time.time()
    
    # Every 3 seconds, check the request status
    if time.time() - st.session_state.check_timer > 3:
        st.session_state.check_timer = time.time()
        
        # Here you would check the request status from Supabase
        # For now, we'll simulate with a placeholder
        
        # If request is approved
        if st.button("SIMULATE APPROVAL (Remove in production)", key="sim_approval"):
            st.session_state.room_id = st.session_state.pending_room_id
            st.session_state.room_name = st.session_state.pending_room_name
            st.session_state.username = st.session_state.pending_username
            st.session_state.is_host = False
            st.session_state.page = "chat"
            
            # Clean up pending state
            if "pending_request_id" in st.session_state:
                del st.session_state.pending_request_id
            if "pending_room_id" in st.session_state:
                del st.session_state.pending_room_id
            if "pending_room_name" in st.session_state:
                del st.session_state.pending_room_name
            if "pending_username" in st.session_state:
                del st.session_state.pending_username
            
            st.experimental_rerun()
    
    # Cancel button
    if st.button("CANCEL REQUEST", key="cancel_request"):
        # Here you would cancel the request in Supabase
        
        # Clean up session state
        if "pending_request_id" in st.session_state:
            del st.session_state.pending_request_id
        if "pending_room_id" in st.session_state:
            del st.session_state.pending_room_id
        if "pending_room_name" in st.session_state:
            del st.session_state.pending_room_name
        if "pending_username" in st.session_state:
            del st.session_state.pending_username
        
        st.session_state.page = "join"
        st.experimental_rerun()
