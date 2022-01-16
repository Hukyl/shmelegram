# pylint: disable=missing-function-docstring, missing-module-docstring
# pylint: disable=missing-class-docstring, invalid-name, unused-argument

import unittest
from datetime import datetime

from parameterized import parameterized

from shmelegram import db
from shmelegram.config import ChatKind
from shmelegram.models import Chat, User, Message


class DatabaseTestBase(unittest.TestCase):
    def setUp(self):
        db.session = db.create_scoped_session(options={'autocommit': True})
        db.create_all()

    def tearDown(self):
        db.drop_all()


class TestModelMixin(DatabaseTestBase):
    """
    Test `ModelMixin` mixin.

    Only user model is being tested since every other model is a child
        of the same classes as the user one.
    """

    def test_get_or_none(self):
        user = User(username='admin', password='TesT123.-wow')
        db.session.add(user)
        db.session.flush()
        self.assertIsInstance(User.get_or_none(user.id), User)
        self.assertIsNone(User.get_or_none(-1))

    def test_update(self):
        user = User(username='admin', password='TesT123.-wow')
        db.session.add(user)
        db.session.flush()
        dt = datetime(2022, 1, 1)
        self.assertEqual(user.username, 'admin')
        self.assertTrue(user.check_password('TesT123.-wow'))
        self.assertNotEqual(user.last_online, dt)
        user.update({
            'username': 'random', 'password': 'TesT123.-gas',
            'last_online': dt
        })
        self.assertEqual(user.username, 'random')
        self.assertTrue(user.check_password('TesT123.-gas'))
        self.assertEqual(user.last_online, dt)

    def test_save(self):
        user = User(username='admin', password='TesT123.-wow')
        self.assertIsNone(user.id)
        user.save()
        self.assertIsInstance(user.id, int)

    def test_delete(self):
        user = User(username='admin', password='TesT123.-wow')
        db.session.add(user)
        db.session.flush()
        self.assertIsInstance(
            User.query.filter_by(id=user.id).first(), User
        )
        user.delete()
        self.assertIsNone(
            User.query.filter_by(id=user.id).first()
        )

    def test_get(self):
        user = User(username='admin', password='TesT123.-wow')
        self.assertIsNone(user.id)
        with self.assertRaises(ValueError):
            User.get(user.id)
        db.session.add(user)
        db.session.flush()
        self.assertIsNotNone(user.id)
        self.assertIsInstance(User.get(user.id), User)

    def test_exists(self):
        user = User(username='admin', password='TesT123.-wow')
        db.session.add(user)
        db.session.flush()
        self.assertTrue(User.exists(user.id))
        self.assertFalse(User.exists(-1))


class TestChats(DatabaseTestBase):
    def test_invalid_initialization(self):
        """
        Test if raises errors if different chat types are initialized
            meeting required conditions.
        """
        with self.assertRaises(ValueError):
            Chat(kind=ChatKind.GROUP)
        with self.assertRaises(ValueError):
            Chat(kind=ChatKind.PRIVATE, title='Some Title')

    @parameterized.expand([
        ('private', Chat(kind=ChatKind.PRIVATE)),
        ('group', Chat(kind=ChatKind.GROUP, title='some title'))
    ])
    def test_user_chat_membership(self, name: str, chat: Chat):
        user = User(username='admin', password='TesT123.-wow')
        db.session.add_all([chat, user])
        chat.add_member(user)
        self.assertIn(chat, user.chats)
        self.assertIn(user, chat.members)
        chat.remove_member(user)
        self.assertNotIn(chat, user.chats)
        self.assertNotIn(user, chat.members)

    @parameterized.expand([
        ('private', Chat(kind=ChatKind.PRIVATE)),
        ('group', Chat(kind=ChatKind.GROUP, title='some title'))
    ])
    def test_delete_cascade(self, name: str, chat: Chat):
        """
        Test if chat is deleted, all related messages are deleted either.
        Also test if users who are members of the chat are not deleted.
        """
        user = User(username='admin', password='TesT123.-wow')
        db.session.add_all([chat, user])
        message1 = Message(from_user=user, chat=chat, text='message 1 text')
        message2 = Message(from_user=user, chat=chat, text='message 2 text')
        message3 = Message(from_user=user, chat=chat, text='message 3 text')
        db.session.add_all([message1, message2, message3])
        db.session.flush()
        messages_ids = (message3.id, message2.id, message1.id)
        self.assertListEqual(
            chat.messages.all(), [message3, message2, message1]
        )
        db.session.delete(chat)
        db.session.flush()
        self.assertTrue(all(
            not db.session.query(
                Message.query.filter(Message.id == x).exists()
            ).scalar() for x in messages_ids
        ))
        self.assertTrue(db.session.query(
            User.query.filter(User.id == user.id).exists()
        ).scalar())


class TestMessages(DatabaseTestBase):
    @parameterized.expand([
        ('private', Chat(kind=ChatKind.PRIVATE)),
        ('group', Chat(kind=ChatKind.GROUP, title='some title'))
    ])
    def test_view_message_by_nonmember(self, name: str, chat: Chat):
        """
        Test if user who is not a member of a chat, where message was created,
        can view it.
        """
        user = User(username='admin', password='TesT123.-wow')
        db.session.add_all([chat, user])
        message = Message(from_user=user, chat=chat, text="some text")
        db.session.add(message)
        with self.assertRaises(ValueError):
            message.add_view(user)

    @parameterized.expand([
        ('private', Chat(kind=ChatKind.PRIVATE)),
        ('group', Chat(kind=ChatKind.GROUP, title='some title'))
    ])
    def test_seen_messages(self, name: str, chat: Chat):
        """
        Test if users who seen message would not be deleted on message deletion
        """
        user = User(username='admin', password='TesT123.-wow')
        db.session.add_all([chat, user])
        chat.add_member(user)
        message = Message(from_user=user, chat=chat, text='123')
        message.add_view(user)
        db.session.add(message)
        db.session.flush()
        self.assertTrue(db.session.query(
            User.query.filter(User.id == user.id).exists()
        ).scalar())
        db.session.delete(message)
        db.session.flush()
        self.assertTrue(db.session.query(
            User.query.filter(User.id == user.id).exists()
        ).scalar())
        self.assertFalse(db.session.query(
            Message.query.filter(Message.id == message.id).exists()
        ).scalar())
