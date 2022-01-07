from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat, User
from shmelegram.service import ChatService, UserService


class UserBaseApi(Resource):
    NOT_EXISTS_MESSAGE = "User {} does not exist"
    EMPTY_MESSAGE = {'success': True}
    service = UserService


@api.resource('/users')
class UserListApi(UserBaseApi):
    def get(self):
        page = request.args.get('page', 1, int)
        startswith_name = request.args.get('startwith', '', str)
        return {'users': self.service.get_list(
            startwith=startswith_name, page=page
        )}, 200



@api.resource('/users/<int:user_id>')
class UserApi(UserBaseApi):
    def get(self, user_id):
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        return self.service.to_json(user), 200

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
        return self.service.to_json(user), 202

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
        if not User.exists(user_id):
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        return {
            'chats': self.service.get_user_chats(user_id)
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
        if not User.exists(user_id):
            return self.NOT_EXISTS_MESSAGE.format(user_id), 404
        elif not Chat.exists(chat_id):
            return f"Chat {chat_id} does not exist", 404
        return {'messages': ChatService.get_unread_messages(
            chat_id, user_id
        )}, 200
