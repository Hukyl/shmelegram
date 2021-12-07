from typing import Any

from flask_socketio import send, emit, join_room, leave_room

from shmelegram.models import User, Chat, Message
from shmelegram import socketio


# Sending messages data object must contain 'chat_id', 'user_id'

def mark_message_deliver(data: dict[str, Any]):
    """
    Callback function to mark the delivered message
    
    Args:
        data (dict[str, Any]): Description
    """
    pass


@socketio.on('connect')
def connect(data: dict[str, Any]):
    pass


@socketio.on('message')
def send_message(data: dict[str, Any]):
    """
    Must contain `chat_id`, `user_id`, `is_service` and `text`
    
    Args:
        data (dict[str, Any]): Description
    """
    chat_id = data.pop('chat_id')
    send(data, json=True, to=chat_id, callback=mark_message_deliver)


@socketio.on('disconnect')
def disconnect(data: dict[str, Any]):
    pass
