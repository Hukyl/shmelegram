from typing import Any

from flask_socketio import send, emit, join_room, leave_room
from sqlalchemy.orm import load_only

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
    user_id = data['user_id']
    user = User.get(user_id)
    for chat in user.chats.options(load_only("id")).all():
        join_room(chat.id)


@socketio.event
def join_chat(data: dict[str, Any]):
    chat_id = data['chat_id']
    join_room(chat_id)


@socketio.event
def leave_chat(data: dict[str, Any]):
    chat_id = data['chat_id']
    leave_room(chat_id)


@socketio.on('message')
def send_message(data: dict[str, Any]):
    """
    Must contain `chat_id`, `user_id`, `is_service` and `text`
    
    Args:
        data (dict[str, Any]): Description
    """
    chat_id = data.pop('chat_id')
    send(data, json=True, to=chat_id, callback=mark_message_deliver)

