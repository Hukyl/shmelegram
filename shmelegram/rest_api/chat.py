from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat
from shmelegram.service import ChatService


class ChatBaseApi(Resource):
    service = ChatService


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
        return ChatService.to_json(chat), 200

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
        return ChatService.to_json(chat), 202

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
        page = request.args.get('page', 1, int)
        startswith_name = request.args.get('startwith', '', str)
        return {'chats': self.service.get_list(
            startwith=startswith_name, page=page
        )}, 200
