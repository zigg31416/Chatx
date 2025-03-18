import os
import json
import time
import uuid
import redis
import streamlit as st
from datetime import datetime, timedelta

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

# Key prefixes for different data types
CHATROOM_PREFIX = "chatroom:"
MESSAGE_PREFIX = "message:"
REQUEST_PREFIX = "request:"

# Chatroom expiration time (24 hours)
CHATROOM_EXPIRY = 60 * 60 * 24

def create_chatroom(name, host_name):
    """Create a new chatroom and return its code and ID"""
    client = get_redis_client()
    
    # Generate a random 5-digit code
    import random
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

# ----- Real-time message subscription (uses thread-safe callback) -----

def listen_for_messages(chatroom_id, callback):
    """
    Listen for new messages in a chatroom
    
    This should be run in a separate thread
    """
    client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    pubsub = client.pubsub()
    
    # Subscribe to messages channel
    pubsub.subscribe(f"messages:{chatroom_id}")
    
    # Listen for messages
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                callback(data)
            except Exception as e:
                print(f"Error processing message: {e}")
    
    pubsub.unsubscribe()

def listen_for_requests(chatroom_id, callback):
    """
    Listen for new join requests in a chatroom
    
    This should be run in a separate thread
    """
    client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
    pubsub = client.pubsub()
    
    # Subscribe to join requests channel
    pubsub.subscribe(f"join-requests:{chatroom_id}")
    
    # Listen for messages
    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                data = json.loads(message["data"])
                callback(data)
            except Exception as e:
                print(f"Error processing request: {e}")
    
    pubsub.unsubscribe()