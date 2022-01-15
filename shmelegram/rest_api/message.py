"""
This module provides REST API classes for message interactions.
Defines following classes:
    - `MessageBaseApi`
    - `MessageApi`
    - `ChatMessagesApi`
"""

from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Message
from shmelegram.service import ChatService, MessageService
from shmelegram.rest_api import JsonDict, StatusCode


class MessageBaseApi(Resource):
    """
    Message Base API class.
    Is parent class for all other message API classes.

    Class attributes:
        service (Type[MessageService]): service for database interactions.
        NOT_EXISTS_MESSAGE (str)
        EMPTY_MESSAGE (JsonDict)
    """
    service = MessageService
    NOT_EXISTS_MESSAGE = "Message {} does not exist"
    EMPTY_MESSAGE = {'success': True}


@api.resource('/messages/<int:message_id>')
class MessageApi(MessageBaseApi):
    """
    API class for Message Interactions.
    """

    def get(self, message_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Returns json data of message giver message id.

        If such message does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Args:
            message_id (int): message's id to fetch

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), StatusCode(404)
        return self.service.to_json(message), StatusCode(200)

    def post(self, message_id: int) -> tuple[JsonDict, StatusCode]:
        """
        POST request handler.
        Update message's data passed in json and return new message's data.

        If such message does not exist, return not exists message and 404 status code.
        Otherwise return json data and 202 status code.

        Args:
            message_id (int): message's id to fetch

        Returns:
            tuple[JsonDict, StatusCode]
        """
        json = request.json or {}
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), StatusCode(404)
        message.update(json)
        return self.EMPTY_MESSAGE, StatusCode(202)

    def delete(self, message_id: int) -> tuple[JsonDict, StatusCode]:
        """
        DELETE request handler.
        Delete message by given id.

        If such message does not exist, return not exists message and 404 status code.
        Otherwise return succes json and 202 status code.

        Args:
            message_id (int): message's id to fetch

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), StatusCode(404)
        message.delete()
        return self.EMPTY_MESSAGE, StatusCode(202)


@api.resource('/messages/chat/<int:chat_id>')
class ChatMessagesApi(MessageBaseApi):
    """
    API class for messages in certain chat interactions.
    """

    def get(self, chat_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Get chat messages from latest to oldest split in pages.
        Page is passed as an url parameter 'page'.

        Args:
            chat_id (int): fetch messages from chat by given this id.

        Returns:
            tuple[JsonDict, StatusCode]
        """
        page = request.args.get('page', 1, int)
        return {'messages': ChatService.get_chat_messages(
            chat_id, page=page
        )}, StatusCode(200)
