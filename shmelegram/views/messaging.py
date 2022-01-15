"""
This module contains socketio event handlers for chat functioning.
All client-to-server events have the same name as function handler names.
Defines following functions:
    - `edit_message`
    - `delete_message`
    - `add_view`
    - `is_offline`
    - `is_online`
    - `connect`
    - `disconnect`
    - `join_chat`
    - `leave_chat`
    - `create_group`
    - `create_private`
    - `send_message` ('message' event)
"""

from datetime import datetime
from typing import Any

from flask import request
from flask_socketio import emit, join_room, leave_room, send, close_room
from sqlalchemy.orm import load_only

from shmelegram import socketio, redis_client
from shmelegram.config import ChatKind
from shmelegram.models import Chat, Message, User
from shmelegram.service import UserService, ChatService, MessageService


JsonDict = dict[str, Any]


@socketio.event
def edit_message(data: JsonDict):
    """
    Edit message event.
    Accepts a dict containing 'message_id' (int),
        'edited_at' (datetime) and 'text' (str).
    Checks if current user is the user that created the message, otherwise ignores event.
    Emits 'edit_message' event to chat member clients
        with same data plus 'chat_id' (int) of message.

    Args:
        data (JsonDict)
    """
    message = Message.get(data['message_id'])
    if int(redis_client.get(request.sid)) != message.from_user.id:
        return
    edited_at = datetime.strptime(data['edited_at'], "%Y-%m-%dT%H:%M:%S")
    message.text = data['text']
    message.edited_at = edited_at
    message.save()
    emit(
        'edit_message', data | {"chat_id": message.chat.id},
        to=message.chat.id
    )


@socketio.event
def delete_message(data: JsonDict):
    """
    Delete message event.
    Accepts a dict containing 'message_id' (int).
    Emits 'delete_message' event to chat member clients
        with same data plus 'chat_id' (int) of message.

    Args:
        data (JsonDict)
    """
    message_id = data['message_id']
    message = Message.get(message_id)
    data['chat_id'] = message.chat.id
    message.delete()
    emit('delete_message', data, to=message.chat.id)


@socketio.event
def add_view(data: JsonDict):
    """
    Add a view to message.
    Accepts a dict containing 'message_id' (int).
    User id is fetched from Redis Storage by `request.sid`.
    Emits 'update_view' event to chat member clients
        with same data plus 'chat_id' (int) of message and 'user_id' (int) from Redis.

    Args:
        data (JsonDict)
    """
    message_id = data['message_id']
    user = User.get(int(redis_client.get(request.sid)))
    message = Message.get(message_id)
    message.add_view(user)
    message.save()
    emit(
        'update_view', data | {'chat_id': message.chat.id, 'user_id': user.id},
        to=message.chat.id
    )


@socketio.event
def is_offline():
    """
    Sets user offline status.
    User id is retrieved from Redis by `request.sid`.
    Accepts no args.
    Emits global 'update_user_status' event with 'user_id' (int) of user
        and 'last_online' (datetime to str).
    """
    user = User.get(int(redis_client.get(request.sid)))
    user.last_online = datetime.utcnow()
    user.save()
    socketio.emit('update_user_status', {
        'user_id': user.id, 'last_online': user.last_online.strftime("%Y-%m-%dT%H:%M:%S")
    })


@socketio.event
def is_online():
    """
    Sets user online status.
    User id is retrieved from Redis by `request.sid`.
    Accepts no args.
    Emits global 'update_user_status' event with 'user_id' (int) of user
        and 'last_online' (None).
    """
    user = User.get(int(redis_client.get(request.sid)))
    user.last_online = None
    user.save()
    socketio.emit('update_user_status', {
        'user_id': user.id, 'last_online': None
    })


@socketio.on('connect')
def connect():
    """
    Client connection event handler.
    User id is retrieved through 'user_id' url parameter.
    Accepts no args.
    """
    user_id: int = request.args.get("user_id")
    user = User.get(user_id)
    for chat in user.chats.options(load_only("id")).all():
        join_room(chat.id)
    redis_client.set(request.sid, user_id)
    redis_client.set(user_id, request.sid)
    is_online()


@socketio.on('disconnect')
def disconnect():
    """
    Client disconnection event handler.
    User id is retrieved via Redis.
    Accepts no args.
    """
    user_id = redis_client.get(request.sid)
    is_offline()
    redis_client.delete(request.sid, user_id)


@socketio.event
def join_chat(data: JsonDict):
    """
    Join chat event handler.
    User id is retrieved either by Redis through `request.sid` or by 'user_id' `data` key.
    Accepts data dict containing 'chat_id' (int) and 'user_id' (int, optional).
    Emits:
        'add_member` for chat members with 'user' (JsonDict) and 'chat_id' (int) data;
        'message' for chat members;
        'add_chat' for user with data of chat.

    Args:
        data (JsonDict)
    """
    chat_id = data['chat_id']
    user = User.get(
        data.get('user_id') or int(redis_client.get(request.sid))
    )
    sid = redis_client.get(user.id)
    chat = Chat.get(chat_id)
    chat.add_member(user)
    chat.save()
    message = Message(
        chat=chat, from_user=user, is_service=True,
        text=f"{user.username} joined the group"
    )
    message.save()
    emit(
        'add_member', {'user': UserService.to_json(user), 'chat_id': chat_id},
        to=chat_id, skip_sid=sid
    )
    send(MessageService.to_json(message), to=chat_id)
    join_room(chat_id, sid=sid)
    emit('add_chat', ChatService.to_json(chat), to=sid)


@socketio.event
def leave_chat(data: JsonDict):
    """
    Leave chat event handler.
    User id is retrieved either by Redis through `request.sid` or by 'user_id' `data` key.
    Accepts data dict containing 'chat_id' (int) and 'user_id' (int, optional).
    If chat is private or chat member count is less than 1, chat is deleted.
    Emits:
        'remove_member` for chat members with 'user' (JsonDict) and 'chat_id' (int) data;
        'message' for chat members;
        'remove_chat' with 'chat_id' (int) if meets certain conditions.

    Args:
        data (JsonDict)
    """
    chat_id = data['chat_id']
    user = User.get(
        data.get('user_id') or int(redis_client.get(request.sid))
    )
    chat = Chat.get(chat_id)
    chat.remove_member(user)
    chat.save()
    leave_room(chat_id)
    emit('remove_chat', {'chat_id': chat_id}, to=request.sid)
    if chat.kind is not ChatKind.PRIVATE and chat.member_count:
        message = Message(
            chat=chat, from_user=user, is_service=True,
            text=f"{user.username} left the group"
        )
        message.save()
        emit(
            'remove_member', {'user_id': user.id, 'chat_id': chat.id},
            to=chat_id, skip_sid=request.sid
        )
        send(MessageService.to_json(message), to=chat_id)
    else:
        emit('remove_chat', {'chat_id': chat_id}, to=chat_id, skip_sid=request.sid)
        close_room(chat_id)
        chat.delete()


@socketio.event
def create_group(data: JsonDict):
    """
    Create group event handler.
    User id is retrieved by Redis via `request.sid`.
    Accepts data dict containing 'title' (str).
    Emits 'add_chat' to newly created chat for current user with chat data.

    Args:
        data (JsonDict)
    """
    title = data['title']
    chat = Chat(kind=ChatKind.GROUP, title=title)
    user = User.get(int(redis_client.get(request.sid)))
    chat.save()
    chat.add_member(user)
    message = Message(
        chat=chat, from_user=user, is_service=True,
        text=f'{user.username} created "{title}" group'
    )
    message.save()
    chat.save()
    join_room(chat.id)
    emit('add_chat', ChatService.to_json(chat), to=chat.id)


@socketio.event
def create_private(data: JsonDict):
    """
    Create private chat event handler.
    User id is retrieved by Redis via `request.sid`.
    Accepts data dict containing 'user_id' (int) of companion user.
    Emits 'add_chat' to newly created chat for current and companion users with chat data.

    Args:
        data (JsonDict)
    """
    chat = Chat(kind=ChatKind.PRIVATE)
    users = User.get(int(data['user_id'])), User.get(
        int(redis_client.get(request.sid))
    )
    chat.save()
    for user in users:
        chat.add_member(user)
    message = Message(
        chat=chat, from_user=users[0], is_service=True,
        text='Private chat created'
    )
    message.save()
    chat.save()
    for user in users:
        join_room(chat.id, sid=redis_client.get(user.id))
    emit('add_chat', ChatService.to_json(chat), to=chat.id)


@socketio.on('message')
def send_message(data: JsonDict):
    """
    Message event handler.
    User id is retrieved via Redis through `request.sid`.
    Accepts data dict with following keys:
        'chat_id' (int): chat where message belongs;
        'created_at' (str from datetime): when was message created;
        'is_service' (bool, optional): if message is service;
        'reply_to' (int, optional): message's id for which current message is a reply;
        'text' (str): message text.
    Current user is set to have viewed the message.
    Emits 'message' event to chat member clients with message data.

    Args:
        data (JsonDict)
    """
    chat = Chat.get(data['chat_id'])
    user = User.get(int(redis_client.get(request.sid)))
    created_at = datetime.strptime(data['created_at'], '%Y-%m-%dT%H:%M:%S')
    reply_to = Message.get_or_none(data.get('reply_to'))
    message = Message(
        chat=chat, from_user=user,
        is_service=data.get('is_service', False), text=data['text'],
        reply_to=reply_to, created_at=created_at
    )
    message.save()
    message.add_view(user)
    message.save()
    send(MessageService.to_json(message), to=chat.id)
