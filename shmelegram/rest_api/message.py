import requests
from flask import jsonify, request, url_for
from flask_restful import Resource, abort

from shmelegram import api, db, Config
from shmelegram.models import Chat, Message, User
from shmelegram.schema import ChatSchema, MessageSchema


class MessageBaseApi(Resource):
    schema = MessageSchema()
    NOT_EXISTS_MESSAGE = "Message {} does not exist"
    EMPTY_MESSAGE = {'success': True}


@api.resource('/messages/<int:message_id>')
class MessageApi(MessageBaseApi):
    def get(self, message_id: int):
        try:
            message = Message.get(message_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(message_id), 404
        return self.schema.dump(message)

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
        json = request.json or {}
        page = json.get('page', 1)
        chat = Chat.get(requests.get(
            url_for('api.chatapi', chat_id=chat_id, _external=True)
        ).json()['id'])
        messages = chat.messages.offset(
            (page - 1) * Config.MESSAGE_PAGE_SIZE
        ).limit(Config.MESSAGE_PAGE_SIZE).all()
        return {'messages': [
            self.schema.dump(message) for message in messages
        ]}
