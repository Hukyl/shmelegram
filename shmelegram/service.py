from abc import ABC
from typing import Any

from shmelegram import db
from shmelegram.config import Config
from shmelegram.models import Chat, User
from shmelegram.schema import ChatSchema, MessageSchema, UserSchema

JsonDict = dict[str, Any]


class BaseService(ABC):
    schema = ...

    @classmethod
    def to_json(cls, model: db.Model):
        return cls.schema.dump(model)


class UserService(BaseService):
    schema = UserSchema(exclude=['password'])

    @classmethod
    def get_list(cls, *, startwith: str = '', page: int = 1) -> list[JsonDict]:
        users = User.query.filter(User.username.startswith(startwith)).offset(
            (page - 1) * Config.API_RESPONSE_SIZE
        ).limit(Config.API_RESPONSE_SIZE).all()
        return cls.schema.dump(users, many=True)

    @classmethod
    def get_user_chats(cls, user_id: int) -> list[JsonDict]:
        return ChatService.schema.dump(User.get(user_id).chats.all(), many=True)


class ChatService(BaseService):
    schema = ChatSchema(exclude=['messages'])

    @classmethod
    def get_list(cls, *, startwith: str = '', page: int = 1) -> list[JsonDict]:
        chats = Chat.query.filter(Chat.title.startswith(startwith)).offset(
            (page - 1) * Config.API_RESPONSE_SIZE
        ).limit(Config.API_RESPONSE_SIZE).all()
        return cls.schema.dump(chats, many=True)

    @classmethod
    def get_chat_messages(cls, chat_id: int, /, *, page: int = 1) -> list[JsonDict]:
        chat = Chat.get(chat_id)
        messages = chat.messages.offset(
            (page - 1) * Config.API_RESPONSE_SIZE
        ).limit(Config.API_RESPONSE_SIZE).all()
        return MessageService.schema.dump(messages, many=True)

    @classmethod
    def get_unread_messages(cls, chat_id: int, user_id: int) -> list[int]:
        chat = Chat.get(chat_id)
        user = User.get(user_id)
        return [x.id for x in chat.get_unread_messages(user)]


class MessageService(BaseService):
    schema = MessageSchema()
