from typing import Any
from datetime import datetime

from flask import request
from flask_socketio import send, emit, join_room, leave_room
from sqlalchemy.orm import load_only

from shmelegram.models import User, Chat, Message
from shmelegram import socketio


def datetime_to_str(dt: datetime) -> str:
    return str(dt).replace(' ', 'T')


@socketio.event
def add_view(data: dict[str, Any]):
    user_id = data['user_id']
    message_id = data['message_id']
    user = User.get(user_id)
    message = Message.get(message_id)
    message.add_view(user)
    message.save()
    emit(
        'update_view', data | {'chat_id': message.chat.id}, 
        to=message.chat.id, skip_sid=request.sid
    )


@socketio.event
def is_offline(data: dict[str, Any]):
    user_id = data['user_id']
    user = User.get(user_id)
    user.last_online = datetime.utcnow()
    user.save()
    socketio.emit('update_user_status', {
        'user_id': user.id, 'last_online': datetime_to_str(user.last_online)
    })


@socketio.event
def is_online(data: dict[str, Any]):
    user_id = data['user_id']
    user = User.get(user_id)
    user.last_online = None
    user.save()
    socketio.emit('update_user_status', {
        'user_id': user.id, 'last_online': None
    })    


@socketio.on('connect')
def connect():
    user_id: int = request.args.get("user_id")
    user = User.get(user_id)
    for chat in user.chats.options(load_only("id")).all():
        join_room(chat.id)
    is_online({'user_id': user_id})


@socketio.event
def join_chat(data: dict[str, Any]):
    user_id = data['user_id']
    chat_id = data['chat_id']
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
    user_id = data['user_id']
    chat_id = data['chat_id']
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
    message_id = data['message_id']
    text = data['text']
    message = Message.get(message_id)
    message.text = text
    message.save()
    chat_id = message.chat.id
    emit('update_message', {'message': message_id, 'text': text}, to=chat_id)


@socketio.on('message')
def send_message(data: dict[str, Any]):
    chat_id = data['chat_id']
    user_id = data['user_id']
    is_service = data['is_service']
    text = data['text']
    reply_to_id = data['reply_to']
    created_at = datetime.strptime(data['created_at'], '%Y-%m-%dT%H:%M:%S')
    reply_to = Message.get_or_none(reply_to_id)
    message = Message(
        chat=Chat.get(chat_id), from_user=User.get(user_id), 
        is_service=is_service, text=text, reply_to=reply_to,
        created_at=created_at
    )
    message.save()
    send(
        {"message_id": message.id}, json=True, to=chat_id, 
        skip_sid=request.sid
    )

