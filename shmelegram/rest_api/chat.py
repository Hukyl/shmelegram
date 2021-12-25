from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat
from shmelegram.schema import ChatSchema


class ChatBaseApi(Resource):
    schema = ChatSchema(exclude=['messages'])


@api.resource('/chats/<int:chat_id>')
class ChatApi(ChatBaseApi):
    NOT_EXISTS_MESSAGE = "Chat {} does not exist"
    EMPTY_MESSAGE = {'success': True}

    def get(self, chat_id) -> tuple:
        """
        Get chat by certain id

        Returns:
            tuple[dict, int]: data of chat and a 200 status code
        """
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), 404
        return self.schema.dump(chat), 200

    def post(self, chat_id):
        """
        Update chat by data in `request.json`

        Returns:
            tuple[dict, int]: new data of model and 200 status code
        """
        json = request.json or {}
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), 404
        chat.update(json)
        return self.schema.dump(chat), 202

    def delete(self, chat_id):
        """
        Delete chat by certain id.

        Returns:
            tuple[str, int]: no response with 202 status code
        """
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), 404
        chat.delete()
        return self.EMPTY_MESSAGE, 202


@api.resource('/chats')
class ChatListApi(ChatBaseApi):
    def get(self):
        json = request.json or {}
        startswith_name = json.get('startwith', '')
        return {'chats': [
            self.schema.dump(chat) for chat in Chat.startwith(startswith_name)
        ]}, 200
