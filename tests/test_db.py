import pytest
from sqlalchemy.sql.functions import user

from shmelegram.models import Chat, User, Message, ChatKind


def get_chats():
    return (
        Chat(kind=ChatKind.PRIVATE), 
        Chat(kind=ChatKind.GROUP, title='some title')
    )


def test_create_group_chat_without_title(db):
    """
    Test if can create group chat without title

    Args:
        db ([type]): pytest fixture
    """
    with pytest.raises(
                ValueError, 
                match='unable to create non-private chat without title'
            ):
        Chat(kind=ChatKind.GROUP)


def test_create_private_chat_with_title(db):
    """
    Test if can create private chat with title

    Args:
        db ([type]): pytest fixture
    """
    with pytest.raises(
                ValueError, 
                match='unable to set title in private chat'
            ):
        Chat(kind=ChatKind.PRIVATE, title='Some Title')


@pytest.mark.parametrize("chat", get_chats())
def test_user_chat_membership(db, chat: Chat, user: User):
    """
    Test if adding members to chat with display in member's chats

    Args:
        db ([type]): pytest fixture
        chat (Chat): get function
        user (User): pytest fixture
    """
    db.session.add_all([chat, user])
    chat.add_member(user)
    assert chat in user.chats


@pytest.mark.parametrize("chat", get_chats())
def test_delete_chat_cascade(db, chat: Chat, user: User):
    """
    Test if chat is deleted, all related messages are deleted either
    Also test if users who are members of the chat are not deleted

    Args:
        db ([type]): pytest fixture
        chat (Chat): get function
        user (User): pytest fixture
    """
    db.session.add_all([chat, user])
    message1 = Message(from_user=user, chat=chat, text='message 1 text')
    message2 = Message(from_user=user, chat=chat, text='message 2 text')
    message3 = Message(from_user=user, chat=chat, text='message 3 text')
    messages_ids = (message1.id, message2.id, message3.id)
    db.session.add_all([message1, message2, message3])
    assert chat.messages.all() == [message1, message2, message3]
    db.session.delete(chat)
    db.session.flush()
    assert all(
        not db.session.query(
            Message.query.filter(Message.id == x).exists()
        ).scalar() for x in messages_ids
    )
    assert db.session.query(
        User.query.filter(User.id == user.id).exists()
    ).scalar()


@pytest.mark.parametrize("chat", get_chats())
def test_view_message_by_nonmember(db, chat: Chat, user: User):
    """
    Test if user who is not a member of a chat, where message was created,
    can view it.

    Args:
        db ([type]): pytest fixture
        chat (Chat): get function
        user (User): pytest fixture
    """
    db.session.add_all([chat, user])
    message = Message(from_user=user, chat=chat, text="some text")
    db.session.add(message)
    with pytest.raises(ValueError, match="cannot add view by non-member user"):
        message.add_view(user)
    


@pytest.mark.parametrize("chat", get_chats())
def test_seen_messages(db, chat: Chat, user: User):
    """
    Test if users who seen message would not be deleted on message deletion

    Args:
        db ([type]): pytest fixture
        chat (Chat): get function
        user(User): pytest fixture
    """
    db.session.add_all([chat, user])
    chat.add_member(user)
    message = Message(from_user=user, chat=chat, text='123')
    message.add_view(user)
    db.session.add(message)
    assert db.session.query(
        User.query.filter(User.id == user.id).exists()
    ).scalar()
    db.session.delete(message)
    db.session.flush()
    assert db.session.query(
        User.query.filter(User.id == user.id).exists()
    ).scalar()
    assert not db.session.query(
        Message.query.filter(Message.id == message.id).exists()
    ).scalar()
    