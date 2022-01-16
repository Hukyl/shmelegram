# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=missing-class-docstring, invalid-name, unused-argument

import http
import unittest
from unittest.mock import patch

from parameterized import parameterized

from shmelegram import app, db
from shmelegram.models import Chat, User, Message, ChatKind
from shmelegram.service import UserService, ChatService, MessageService
from shmelegram.rest_api import (
    user as user_api, chat as chat_api, message as message_api
)


db.drop_all()
db.create_all()
user_1 = User(username='ruser1', password="rUser1_")
user_2 = User(username='ruser2', password="rUser2_")
user_3 = User(username='ruser3', password="rUser3_")
chat_group = Chat(kind=ChatKind.GROUP, title='Group 1')
chat_private = Chat(kind=ChatKind.PRIVATE)
chat_group.add_member(user_1)
chat_group.add_member(user_3)
chat_private.add_member(user_2)
chat_private.add_member(user_1)
msg_1 = Message(
    from_user=user_1, chat=chat_group, text='text1'
)
msg_2 = Message(
    from_user=user_3, chat=chat_group, text='text2'
)
msg_3 = Message(
    from_user=user_2, chat=chat_private, text='text2'
)


class ApiBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()


class UserApiTestCase(ApiBaseTestCase):
    def test_get_list(self):
        mock_return_value = [
            UserService.to_json(user) for user in (
                user_1, user_2, user_3
            )
        ]
        with patch(
            'shmelegram.rest_api.user.UserService.get_list', autospec=True,
            return_value=mock_return_value
        ):
            response = self.client.get('/api/users?startwith=ruse')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(response.json, {'users': mock_return_value})

    @parameterized.expand([(user_1, ), (user_2, ), (user_3, )])
    def test_get_user(self, mock_return_value: User):
        with patch(
            'shmelegram.rest_api.user.User.get', autospec=True,
            return_value=mock_return_value
        ):
            response = self.client.get('/api/users/1')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(
                response.json, UserService.to_json(mock_return_value)
            )

    def test_get_user_failure(self):
        with patch(
            'shmelegram.rest_api.user.User.get', autospec=True,
            side_effect=ValueError()
        ):
            response = self.client.get('/api/users/0')
            self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
            self.assertEqual(
                response.json, user_api.UserApi.NOT_EXISTS_MESSAGE
            )


class ChatApiTestCase(ApiBaseTestCase):
    @parameterized.expand([(chat_group, ), (chat_private, )])
    def test_get_chat(self, mock_return_value: Chat):
        with patch(
            'shmelegram.rest_api.chat.Chat.get', autospec=True,
            return_value=mock_return_value
        ):
            response = self.client.get('/api/chats/1')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(
                response.json, ChatService.to_json(mock_return_value)
            )

    def test_get_chat_failure(self):
        with patch(
            'shmelegram.rest_api.chat.Chat.get', autospec=True,
            side_effect=ValueError()
        ):
            response = self.client.get('/api/chats/0')
            self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
            self.assertEqual(
                response.json, chat_api.ChatApi.NOT_EXISTS_MESSAGE
            )

    def test_get_list(self):
        mock_return_value = [ChatService.to_json(chat_group)]
        with patch(
            'shmelegram.rest_api.chat.ChatService.get_list', autospec=True,
            return_value=mock_return_value
        ):
            response = self.client.get('/api/chats?startwith=Gro')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(response.json, {'chats': mock_return_value})


class MessageApiTestCase(ApiBaseTestCase):
    @parameterized.expand([(msg_1, ), (msg_2, ), (msg_3, )])
    def test_get_message(self, mock_return_value: Message):
        with patch(
            'shmelegram.rest_api.message.Message.get', autospec=True,
            return_value=mock_return_value
        ):
            response = self.client.get('/api/messages/1')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(
                response.json, MessageService.to_json(mock_return_value)
            )

    def test_get_message_failure(self):
        with patch(
            'shmelegram.rest_api.message.Message.get', autospec=True,
            side_effect=ValueError()
        ):
            response = self.client.get('/api/messages/0')
            self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
            self.assertEqual(
                response.json, message_api.MessageApi.NOT_EXISTS_MESSAGE
            )

    @parameterized.expand([(chat_group, [msg_1, msg_2]), (chat_private, [msg_3])])
    def test_get_chat_messages(self, chat: Chat, mock_return_value: list[Message]):
        mock_return_value = [
            MessageService.to_json(msg) for msg in mock_return_value
        ]
        with patch(
            'shmelegram.rest_api.message.ChatService.get_chat_messages',
            autospec=True, return_value=mock_return_value
        ):
            response = self.client.get('/api/messages/chat/1')
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertEqual(response.json, {'messages': mock_return_value})
