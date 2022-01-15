"""
This module introduces API classes for chat interactions.
Defines following classes:
    - `ChatBaseApi`
    - `ChatApi`
    - `ChatListApi`
"""

from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat
from shmelegram.service import ChatService
from shmelegram.rest_api import JsonDict, StatusCode



class ChatBaseApi(Resource):
    """
    Base API class for chat interactions.
    Is parent for all other chat API classes.

    Class attributes:
        service (Type[ChatSerice]): service for database interactions.
    """
    service = ChatService


@api.resource('/chats/<int:chat_id>')
class ChatApi(ChatBaseApi):
    """
    API class for chat interactions.

    Class attributes:
        NOT_EXISTS_MESSAGE (str)
        EMPTY_MESSAGE (JsonDict)
    """

    NOT_EXISTS_MESSAGE = "Chat {} does not exist"
    EMPTY_MESSAGE = {'success': True}

    def get(self, chat_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Fetch json chat data by given id.

        If such chat does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), StatusCode(404)
        return ChatService.to_json(chat), StatusCode(200)

    def post(self, chat_id):
        """
        POST request handler.
        Update chat by giver id with json data.

        If such chat does not exist, return not exists message and 404 status code.
        Otherwise return new chat json data and 202 status code.

        Returns:
            tuple[JsonDict, StatusCode]
        """
        json = request.json or {}
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), StatusCode(404)
        chat.update(json)
        return ChatService.to_json(chat), StatusCode(202)

    def delete(self, chat_id):
        """
        DELETE request handler.
        Delete chat by giver id.

        If such chat does not exist, return not exists message and 404 status code.
        Otherwise delete chat, and then return success json and 202 status code.

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(chat_id), StatusCode(404)
        chat.delete()
        return self.EMPTY_MESSAGE, StatusCode(202)


@api.resource('/chats')
class ChatListApi(ChatBaseApi):
    """
    API class for chat list interactions.
    """

    def get(self) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Get list of chats which title startwith some name split into pages.

        Since only group chats have a title, private chats are omitted.
        Title start is passed via 'startwith' url parameter.

        Data is split into pages by size of `Config.API_RESPONSE_SIZE`.
        Numeration starts with 1.

        Returns:
            tuple[JsonDict, StatusCode]: json data and 200 status code
        """
        page = request.args.get('page', 1, int)
        startswith_name = request.args.get('startwith', '', str)
        return {'chats': self.service.get_list(
            startwith=startswith_name, page=page
        )}, StatusCode(200)
