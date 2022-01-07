from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Message
from shmelegram.service import ChatService, MessageService


class MessageBaseApi(Resource):
    service = MessageService
    NOT_EXISTS_MESSAGE = "Message {} does not exist"
    EMPTY_MESSAGE = {'success': True}


@api.resource('/messages/<int:message_id>')
class MessageApi(MessageBaseApi):
    def get(self, message_id: int):
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), 404
        return self.service.to_json(message)

    def post(self, message_id: int):
        json = request.json or {}
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), 404
        message.update(json)
        return self.EMPTY_MESSAGE, 202

    def delete(self, message_id: int):
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), 404
        message.delete()
        return self.EMPTY_MESSAGE, 202


@api.resource('/messages/chat/<int:chat_id>')
class ChatMessagesApi(MessageBaseApi):
    def get(self, chat_id: int):
        page = request.args.get('page', 1, int)
        return {'messages': ChatService.get_chat_messages(
            chat_id, page=page
        )}, 200
