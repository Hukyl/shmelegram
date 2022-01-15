"""
This module introduces API classes for user interactions.
Defines following classes:
    - `UserBaseApi`
    - `UserListApi`
    - `UserApi`
    - `UserChatListApi`
    - `UserChatApi`
    - `UnreadMessagesUserChatApi`
"""

from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat, User
from shmelegram.service import ChatService, UserService
from shmelegram.rest_api import JsonDict, StatusCode


class UserBaseApi(Resource):
    """
    User API base class.
    Is parent for every other user API class.

    Class attributes:
        NOT_EXISTS_MESSAGE (str)
        EMPTY_MESSAGE (JsonDict)
        service (Type[UserService]): service for database interactions
    """
    NOT_EXISTS_MESSAGE = "User {} does not exist"
    EMPTY_MESSAGE = {'success': True}
    service = UserService


@api.resource('/users')
class UserListApi(UserBaseApi):
    """API class for user list interactions."""

    def get(self) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Get list of user whose username startwith some name split into pages.

        Username start is passed via 'startwith' url parameter.

        Data is split into pages by size of `Config.API_RESPONSE_SIZE`.
        Numeration starts with 1.

        Returns:
            tuple[JsonDict, StatusCode]: json data and 200 status code
        """
        page = request.args.get('page', 1, int)
        startswith_name = request.args.get('startwith', '', str)
        return {'users': self.service.get_list(
            startwith=startswith_name, page=page
        )}, StatusCode(200)



@api.resource('/users/<int:user_id>')
class UserApi(UserBaseApi):
    """API class for user interactions."""

    def get(self, user_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Fetch user json data by given id.

        If such user does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Args:
            user_id (int)

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        return self.service.to_json(user), StatusCode(200)

    def post(self, user_id: int) -> tuple[JsonDict, StatusCode]:
        """
        POST request handler.
        Update user by given id with json data.

        The only updateable field is 'last_online'.
        If any other fields are passed, return empty string and 403 status code.

        If such user does not exist, return not exists message and 404 status code.
        Otherwise return new user json data. and 202 status code.

        Args:
            user_id (int)

        Returns:
            tuple[JsonDict, StatusCode]
        """
        json = request.json or {}
        last_online = json.pop('last_online', None)
        if json:
            return '', StatusCode(403)
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        user.last_online = last_online or user.last_online
        user.save()
        return self.service.to_json(user), StatusCode(202)

    def delete(self, user_id: int) -> tuple[JsonDict, StatusCode]:
        """
        DELETE request handler.
        Delete user by given user id.

        If such user does not exist, return not exists message and 404 status code.
        Otherwise return success json and 202 status code.

        Args:
            user_id (int)

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        user.delete()
        return self.EMPTY_MESSAGE, StatusCode(202)


@api.resource('/users/<int:user_id>/chats')
class UserChatListApi(UserBaseApi):
    """API class for list of user's chats interactions."""

    def get(self, user_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Get json data of all chats user is member of.

        If such user does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Args:
            user_id (int): fetch user by this id

        Returns:
            tuple[JsonDict, StatusCode]
        """
        if not User.exists(user_id):
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        return {
            'chats': self.service.get_user_chats(user_id)
        }, StatusCode(200)


@api.resource('/users/<int:user_id>/chats/<int:chat_id>')
class UserChatApi(UserBaseApi):
    """API class for chat which user is member of interactions."""

    def get(self, user_id: int, chat_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Check if user is member of chat or not.

        If such user does not exist, return not exists message and 404 status code.
        If such chat does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Args:
            user_id (int): fetch user by this id
            chat_id (int): fetch chat by this id

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return f"Chat {chat_id} does not exist", StatusCode(404)
        is_member = user in chat.members
        return dict(is_member=is_member), StatusCode(200)

    def delete(
                self, user_id: int, chat_id: int
            ) -> tuple[JsonDict, StatusCode]:
        """
        DELETE request handler.
        Remove user as a member of given chat.

        If user is not a member of given chat, return not member message and 406 status code.

        If such user does not exist, return not exists message and 404 status code.
        If such user does not exist, return not exists message and 404 status code.
        Otherwise return success json and 202 status code.

        Args:
            user_id (int): fetch user by this id
            chat_id (int): fetch chat by this id

        Returns:
            tuple[JsonDict, StatusCode]
        """
        try:
            user = User.get(user_id)
        except ValueError:
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        try:
            chat = Chat.get(chat_id)
        except ValueError:
            return f"Chat {chat_id} does not exist", StatusCode(404)
        if user not in chat.members:
            return (
                f"User {user_id} is not member of Chat {chat_id}",
                StatusCode(406)
            )
        chat.members.remove(user)
        return self.EMPTY_MESSAGE, StatusCode(202)


@api.resource('/users/<int:user_id>/chats/<int:chat_id>/unread')
class UnreadMessagesUserChatApi(UserBaseApi):
    """API class for fetching ids of unread messages in chat by given user."""

    def get(self, user_id: int, chat_id: int) -> tuple[JsonDict, StatusCode]:
        """
        GET request handler.
        Get list of ids of all unread messages sorted in order from latest to oldest
            in chat by given user.

        If such user does not exist, return not exists message and 404 status code.
        If such chat does not exist, return not exists message and 404 status code.
        Otherwise return json data and 200 status code.

        Args:
            user_id (int): fetch user with this id
            chat_id (int): fetch chat with this id

        Returns:
            tuple[JsonDict, StatusCode]:
        """
        if not User.exists(user_id):
            return self.NOT_EXISTS_MESSAGE.format(user_id), StatusCode(404)
        if not Chat.exists(chat_id):
            return f"Chat {chat_id} does not exist", StatusCode(404)
        return {'messages': ChatService.get_unread_messages(
            chat_id, user_id
        )}, StatusCode(200)
