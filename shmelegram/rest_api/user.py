"""
This module introduces API classes for user interactions.
Defines following classes:
    - `UserBaseApi`
    - `UserListApi`
    - `UserApi`
    - `UserChatListApi`
    - `UnreadMessagesUserChatApi`
"""

from flask import request
from flask_restful import Resource

from shmelegram import api
from shmelegram.models import Chat, User
from shmelegram.service import ChatService, UserService
from shmelegram.rest_api import JsonDict, StatusCode
from shmelegram.rest_api.chat import ChatBaseApi


class UserBaseApi(Resource):
    """
    User API base class.
    Is parent for every other user API class.

    Class attributes:
        NOT_EXISTS_MESSAGE (str)
        EMPTY_MESSAGE (JsonDict)
        service (Type[UserService]): service for database interactions
    """
    NOT_EXISTS_MESSAGE = {"error": "User with such id does not exist"}
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
            return self.NOT_EXISTS_MESSAGE, StatusCode(404)
        return self.service.to_json(user), StatusCode(200)


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
            return self.NOT_EXISTS_MESSAGE, StatusCode(404)
        return {
            'chats': self.service.get_user_chats(user_id)
        }, StatusCode(200)


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
            return self.NOT_EXISTS_MESSAGE, StatusCode(404)
        if not Chat.exists(chat_id):
            return ChatBaseApi.NOT_EXISTS_MESSAGE, StatusCode(404)
        return {'messages': ChatService.get_unread_messages(
            chat_id, user_id
        )}, StatusCode(200)
