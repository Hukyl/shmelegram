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
        """
        Get list of users filtered by the start of their usernames.
        Data is split into pages of `Config.API_RESPONSE_SIZE`.

        `page` can take a special value of -1, if so, data will not be split into pages.
        Careful! Can cause MemoryError due to big amount of data.

        If `page` is bigger than max data page, returns empty list.

        Args:
            startwith (str, optional): filter by start of username. Defaults to ''.
            page (int, optional): page of data. Defaults to 1.

        Returns:
            list[JsonDict]: list of json datas of users
        """
        users = User.query.filter(User.username.startswith(startwith))
        if page != -1:
            users = users.offset(
                (page - 1) * Config.API_RESPONSE_SIZE
            ).limit(Config.API_RESPONSE_SIZE)
        return cls.schema.dump(users.all(), many=True)

    @classmethod
    def get_user_chats(cls, user_id: int) -> list[JsonDict]:
        return ChatService.schema.dump(User.get(user_id).chats.all(), many=True)


class ChatService(BaseService):
    schema = ChatSchema(exclude=['messages'])

    @classmethod
    def get_list(cls, *, startwith: str = '', page: int = 1) -> list[JsonDict]:
        """
        Get list of chats filtered by the start of their titles.
        Private chats (title = None) are not returned.
        Data is split into pages of `Config.API_RESPONSE_SIZE`.

        `page` can take a special value of -1, if so, data will not be split into pages.
        Careful! Can cause MemoryError due to big amount of data.

        If `page` is bigger than max data page, returns empty list.        

        Args:
            startwith (str, optional): filter by start of title. Defaults to ''.
            page (int, optional): page of data. Defaults to 1.

        Returns:
            list[JsonDict]: list of json datas of chats
        """        
        chats = Chat.query.filter(Chat.title.startswith(startwith))
        if page != -1:
            chats = chats.offset(
                (page - 1) * Config.API_RESPONSE_SIZE
            ).limit(Config.API_RESPONSE_SIZE)
        return cls.schema.dump(chats.all(), many=True)

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
