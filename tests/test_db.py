import pytest

from shmelegram.models import Chat, User, Message, ChatKind


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
        db ([type]): [description]
    """
    with pytest.raises(
                ValueError, 
                match='unable to set title in private chat'
            ):
        Chat(kind=ChatKind.PRIVATE, title='Some Title')


@pytest.mark.parametrize("chat", [
    Chat(kind=ChatKind.PRIVATE), Chat(kind=ChatKind.GROUP, title='some title')
])
def test_user_chat_membership(db, chat: Chat):
    """
    Test if adding members to chat with display in member's chats

    Args:
        db ([type]): pytest fixture
        chat (Chat): pytest fixture
    """
    user = User(username='username', password='pa$$Word123')
    db.session.add_all([chat, user])
    chat.add_member(user)
    assert chat in user.chats


@pytest.mark.parametrize("chat", [
    Chat(kind=ChatKind.PRIVATE), Chat(kind=ChatKind.GROUP, title='some title')
])
def test_delete_chat_cascade(db, chat: Chat):
    """
    Test if chat is deleted, all related messages are also either
    Also test if users who are members of the chat are not deleted

    Args:
        db ([type]): pytest fixture
        chat (Chat): pytest fixture
    """
    user = User(username='username', password='pa$$Word123')
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
    assert db.session.query(User.query.filter(User.id == user.id).exists()).scalar()
