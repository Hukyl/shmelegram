from typing import Any

from flask_socketio import send, emit, join_room, leave_room
from sqlalchemy.orm import load_only

from shmelegram.models import User, Chat, Message
from shmelegram import socketio


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
    user_id = data['user_id']
    user = User.get(user_id)
    chat = Chat.get(chat_id)
    user.chats.add(chat)
    user.save()
    join_room(chat_id)
    message = Message(
        chat=chat, from_user=user, is_service=True, 
        text=f"{user.username} joined the group"
    )
    message.save()
    send({"message_id": message.id}, json=True, to=chat_id)


@socketio.event
def leave_chat(data: dict[str, Any]):
    chat_id = data['chat_id']
    user_id = data['user_id']
    user = User.get(user_id)
    chat = Chat.get(chat_id)
    user.chats.add(chat)
    user.save()
    leave_room(chat_id)
    message = Message(
        chat=chat, from_user=user, is_service=True, 
        text=f"{user.username} left the group"
    )
    message.save()
    send({"message_id": message.id}, json=True, to=chat_id)    


@socketio.event
def edit_message(data: dict[str, Any]):
    message = Message.get(data['message_id'])
    message.text = data['text']
    message.save()
    chat_id = message.chat.id
    emit('update_message', data, to=chat_id)


@socketio.on('message')
def send_message(data: dict[str, Any]):
    chat_id = data['chat_id']
    user_id = data['user_id']
    is_service = data['is_service']
    reply_to = Message.get_or_none(data['reply_to'])
    text = data['text']
    message = Message(
        chat=Chat.get(chat_id), from_user=User.get(user_id), 
        is_service=is_service, text=text, reply_to=reply_to
    )
    message.save()
    send(
        {"message_id": message.id}, json=True, to=chat_id, 
        callback=mark_message_deliver
    )

