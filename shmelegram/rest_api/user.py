from flask import request, url_for
from sqlalchemy.orm import load_only
from flask_restful import Resource
import requests

from shmelegram import api
from shmelegram.models import Chat, User
from shmelegram.schema import UserSchema


class UserBaseApi(Resource):
    NOT_EXISTS_MESSAGE = "User {} does not exist"
    EMPTY_MESSAGE = {'success': True}
    schema = UserSchema()


@api.resource('/users')
class UserListApi(UserBaseApi):
    def get(self):
        return {'ids': [
            x.id for x in User.query.options(load_only("id")).all()
        ]}, 200



@api.resource('/users/<int:user_id>')
class UserApi(UserBaseApi):
    def get(self, user_id):
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        return self.schema.dump(user), 200

    def post(self, user_id):
        json = request.json or {}
        last_online = json.pop('last_online', None)
        if json:
            return '', 403
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        user.last_online = last_online or user.last_online
        user.save()
        return self.schema.dump(user), 202

    def delete(self, user_id):
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        user.delete()
        return self.EMPTY_MESSAGE, 202


@api.resource('/users/<int:user_id>/chats')
class UserChatListApi(UserBaseApi):
    def get(self, user_id):
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        return {
            'chats': [
                requests.get(
                    url_for('api.chatapi', chat_id=chat.id, _external=True)
                ).json() for chat in user.chats
            ]
        }, 200


@api.resource('/users/<int:user_id>/chats/<int:chat_id>')
class UserChatApi(UserBaseApi):
    def get(self, user_id: int, chat_id: int):
        """
        Check if user is member of chat or not
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return f"Chat {chat_id} does not exist", 404
        is_member = user in chat.members
        return dict(is_member=is_member), 200

    def delete(self, user_id: int, chat_id: int):
        """
        Delete membership of user in chat
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return f"Chat {chat_id} does not exist", 404
        if user not in chat.members:
            return f"User {user_id} is not member of Chat {chat_id}", 406
        chat.members.remove(user)
        return self.EMPTY_MESSAGE, 202


@api.resource('/users/<int:user_id>/chats/<int:chat_id>/unread')
class UnreadMessagesUserChatApi(UserBaseApi):
    def get(self, user_id: int, chat_id: int):
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return f"Chat {chat_id} does not exist", 404
        messages = chat.get_unread_messages(user)
        return {'messages': list(map(lambda x: x.id, messages))}, 200
