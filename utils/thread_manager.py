import threading
import time
import streamlit as st
from utils.redis_client import listen_for_messages, listen_for_requests

class ThreadManager:
    """Manage background threads for Redis pub/sub"""
    
    @staticmethod
    def start_message_listener(chatroom_id, callback):
        """Start a thread to listen for new messages"""
        # Create a thread-safe wrapper for the callback
        def thread_safe_callback(data):
            # Use session state to transfer data from thread to main thread
            if 'new_messages' not in st.session_state:
                st.session_state.new_messages = []
            st.session_state.new_messages.append(data)
        
        # Create and start thread
        thread = threading.Thread(
            target=listen_for_messages,
            args=(chatroom_id, thread_safe_callback),
            daemon=True
        )
        thread.start()
        return thread
    
    @staticmethod
    def start_request_listener(chatroom_id, callback):
        """Start a thread to listen for new join requests"""
        # Create a thread-safe wrapper for the callback
        def thread_safe_callback(data):
            # Use session state to transfer data from thread to main thread
            if 'new_requests' not in st.session_state:
                st.session_state.new_requests = []
            st.session_state.new_requests.append(data)
        
        # Create and start thread
        thread = threading.Thread(
            target=listen_for_requests,
            args=(chatroom_id, thread_safe_callback),
            daemon=True
        )
        thread.start()
        return thread
    
    @staticmethod
    def check_for_updates():
        """Process any updates from background threads"""
        # Check for new messages
        if 'new_messages' in st.session_state and st.session_state.new_messages:
            # Process new messages
            for message in st.session_state.new_messages:
                # Handle message (e.g., play sound, add to chat)
                st.session_state.message_count += 1
            
            # Clear the queue
            st.session_state.new_messages = []
            
            # Trigger a rerun to update the UI
            st.experimental_rerun()
        
        # Check for new join requests
        if 'new_requests' in st.session_state and st.session_state.new_requests:
            # Process new requests
            for request in st.session_state.new_requests:
                # Handle request (e.g., update UI, play sound)
                if request['type'] == 'new_request':
                    st.session_state.last_request_count += 1
            
            # Clear the queue
            st.session_state.new_requests = []
            
            # Trigger a rerun to update the UI
            st.experimental_rerun()