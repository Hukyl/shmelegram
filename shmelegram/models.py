"""
This module contains models in database, this module defines the
following classes:
    - `ModelMixin`, base model mixin used in every other model;
    - `User`, user model;
    - `Chat`, chat model;
    - `Message`, message model.
"""


from __future__ import annotations

from datetime import datetime as dt
from hashlib import sha256
from typing import Any, NoReturn, Optional, TypeVar, Type, Union

from sqlalchemy import (
    Table, Column, Integer, ForeignKey, DateTime, String, Enum, Boolean
)
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import backref, load_only, relationship, validates
from sqlalchemy.schema import CheckConstraint
from flask_sqlalchemy import BaseQuery

from shmelegram import db, utils
from shmelegram.config import ChatKind

ModelType = TypeVar('ModelType', bound='ModelMixin')
ModelId = TypeVar('ModelId')
JsonDict = dict[str, Any]


chat_membership = Table(
    'chat_membership', db.Model.metadata,
    Column(
        'chat_id', Integer, ForeignKey('chat.id', ondelete="CASCADE")
    ),
    Column(
        'user_id', Integer, ForeignKey('user.id', ondelete="CASCADE")
    )
)

message_view = Table(
    'message_view', db.Model.metadata,
    Column(
        'user_id', Integer, ForeignKey('user.id', ondelete="CASCADE")
    ),
    Column(
        'message_id', Integer,
        ForeignKey('message.id', ondelete="CASCADE")
    )
)


class ModelMixin:
    """
    Basic ModelMixin containing different class utilities.
    """

    @classmethod
    def exists(cls, id_: ModelId) -> bool:
        """
        Check if model with this id exists

        Args:
            id_ (int)

        Returns:
            bool
        """
        return db.session.query(
            cls.query.filter(cls.id == id_).exists()
        ).scalar()

    def update(self, data: JsonDict) -> NoReturn:
        """
        Update model according to dict data.

        Args:
            data (JsonDict): data to be updated

        Returns:
            NoReturn
        """
        for key, value in data.items():
            setattr(self, key, value)
        db.session.add(self)

    @classmethod
    def get(cls: Type[ModelType], id_: ModelId) -> ModelType:
        """
        Get model by some id

        Args:
            id_ (int): id of model to be retrieved

        Raises:
            ValueError: if model with such id does not exist.
                Use `exists()` to check if the id exists

        Returns:
            db.Model: model
        """
        model = cls.query.get(id_)
        if model is None:
            raise ValueError(f'{cls.__name__} with id {id_} does not exist')
        return model

    @classmethod
    def get_or_none(cls: Type[ModelType], id_: ModelId) -> Optional[ModelType]:
        """
        Get model by some id. If this id does not exist, return None

        Args:
            id_ (int): id of model to be retrieved

        Returns:
            db.Model: model
        """
        return cls.query.get(id_)

    def delete(self) -> NoReturn:
        """
        Delete model from database and flush the database data.

        Returns:
            NoReturn
        """
        db.session.delete(self)
        db.session.flush()

    def save(self) -> NoReturn:
        """
        Save model to database and flush the database data.

        Returns:
            NoReturn
        """
        db.session.add(self)
        db.session.flush()


class User(db.Model, ModelMixin):
    """
    Model representing user.

    Arguments:
        username (str): user's username. Unique.
        password (str): is stored encrypted using sha256.
        last_online (datetime, optional): last online UTC datetime. Defaults to `datetime.utcnow()`
    """

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True, nullable=False)
    password = Column(String(64), nullable=False)
    last_online = Column(
        DateTime(), default=dt.utcnow,
        nullable=True, onupdate=dt.utcnow
    )  # None means online now

    __table_args__ = (
        CheckConstraint(
            'length(username) > 4', name='username_min_length'
        ),
    )

    def __repr__(self) -> str:
        return self.__class__.__name__ + (
            f"(id={self.id}, username={self.username!r})"
        )

    def update_last_online(self) -> NoReturn:
        """
        Update user's last online to current UTC and save model.

        Returns:
            NoReturn
        """
        self.last_online = dt.utcnow()
        self.save()

    @classmethod
    def get_by_username(cls, username: str, /) -> User:
        """
        Get user by given username.

        Args:
            username (str): user with such username to be retrieved.

        Raises:
            ValueError: if such user does not exist

        Returns:
            User: user with given username
        """
        user = cls.query.filter(cls.username == username).first()
        if user is None:
            raise ValueError(
                f"{cls.__name__} with username {username!r} does not exist"
            )
        return user

    @classmethod
    def username_exists(cls, username: str, /) -> bool:
        """
        Check if user with giver username exists.

        Args:
            username (str)

        Returns:
            bool
        """
        return db.session.query(User.id).filter_by(
                username=username).first() is not None

    @classmethod
    def startwith(cls, name: str = '', /, *, query: bool = False) -> Union[BaseQuery, list[User]]:
        """
        Return all users with whose username startswith `name`.

        Args:
            name (str, optional): username start. Defaults to ''.
            query (bool, optional): to return as `flas_sqlalchemy.BaseQuery`. Defaults to False.

        Returns:
            Union[BaseQuery, list[User]]
        """
        users = cls.query.filter(
            cls.username.startswith(name)
        )
        if not query:
            users = users.all()
        return users

    @hybrid_method
    def check_password(self, password: str) -> bool:
        """
        Check if given password matches the user's password.

        Args:
            password (str)

        Returns:
            bool
        """
        return sha256(password.encode('utf-8')).hexdigest() == self.password

    @validates('username')
    def validate_username(self, key: str, value: str) -> str:
        """
        Validate username. Fires on every username update.

        Args:
            key (str): 'username'
            value (str): username value

        Raises:
            ValueError: if username is invalid

        Returns:
            str: username value
        """
        # pylint: disable=unused-argument
        if not utils.validate_username(value):
            raise ValueError('invalid username')
        return value

    @validates('password')
    def validate_password(self, key: str, value: str) -> str:
        """
        Validate password. Fires on every password update.

        Args:
            key (str): 'password'
            value (str): password value

        Raises:
            ValueError: if password is invalid

        Returns:
            str: password value
        """
        # pylint: disable=unused-argument
        if not utils.validate_password(value):
            raise ValueError('invalid password')
        return sha256(value.encode('utf-8')).hexdigest()


class Chat(db.Model, ModelMixin):
    """
    Model representing chat.

    Arguments:
        kind (ChatKind): type of chat
        title (str, optional): title for group chat

    Raises:
        ValueError: chat is private and has title, or chat is group and no title
    """
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True)
    kind = Column(Enum(ChatKind))
    title = Column(String(50), nullable=True)

    members = relationship(
        'User', secondary=chat_membership, passive_deletes=True,
        backref=backref('chats', lazy='dynamic')
    )
    messages = relationship(
        'Message', lazy='dynamic', backref='chat',
        cascade="all, delete", passive_deletes=True,
        order_by="-Message.created_at"
    )

    def __init__(self, *, kind: ChatKind, title: str = None):
        if kind is ChatKind.PRIVATE and title:
            raise ValueError('unable to set title in private chat')
        elif kind is ChatKind.GROUP and not title:
            raise ValueError('unable to create non-private chat without title')
        super().__init__(kind=kind, title=title)

    @validates('members')
    def validate_member(self, key: str, user: User) -> User:
        """
        Validate member. Fires on every member addition.

        Args:
            key (str): 'members'
            user (User): user to be validated

        Raises:
            ValueError: new member count equals to member limit

        Returns:
            User: user that was validated. Same user as the one was passed.
        """
        # pylint: disable=unused-argument
        member_limit = self.member_limit
        if self.member_count >= member_limit:
            raise ValueError(
                f'member count exceeds member limit ({member_limit})'
            )
        return user

    @hybrid_property
    def member_limit(self) -> int:
        """
        Max member limit property.

        Returns:
            int
        """
        return self.kind.value

    @hybrid_property
    def member_count(self) -> int:
        """
        Current member count property.

        Returns:
            int
        """
        return len(self.members)

    def add_member(self, user: User) -> True:
        """
        Add member to collection. See `validate_member` for errors.

        Args:
            user (User): user to be added.

        Returns:
            True
        """
        self.members.append(user)
        return True

    def remove_member(self, user: User) -> True:
        """
        Remove member from collection.
        If no such user was located in members, ignores the call.

        Args:
            user (User): user to be added.

        Returns:
            True
        """
        self.members.remove(user)
        return True

    def get_unread_messages(self, user: User) -> list[Message]:
        """
        Get unread messages by a user.
        If user not a member of a chat, raise ValueError

        Args:
            user (User): user to be checked

        Returns:
            list[Message]
        """
        if user not in self.members:
            raise ValueError('cannot get messages by non-member user')
        return self.messages.filter(~Message.seen_by.any(User.id == user.id))\
            .options(load_only("id")).all()

    def get_private_title(self, user: User) -> str:
        """
        Get private title for user.
        Title for private chats is None, so the title has to be
            retrieved as the companion user's username.

        Args:
            user (User): user for which the title is retrieved

        Raises:
            ValueError: chat type is not private
            ValueError: user is not member of this chat

        Returns:
            str
        """
        if self.kind is not ChatKind.PRIVATE:
            raise ValueError("cannot get private title of non-private chat")
        members = list(self.members)
        if user not in members:
            raise ValueError('cannot get title for non-member user')
        members.remove(user)
        return members[0].username

    @classmethod
    def get_by_title(cls, title: str, /) -> Chat:
        """
        Get chat by total matching to given title.

        Args:
            title (str)

        Raises:
            ValueError: chat with such title does not exist

        Returns:
            Chat
        """
        chat = cls.query.filter(cls.title == title).first()
        if chat is None:
            raise ValueError(
                f'{cls.__name__} with title {title!r} does not exist'
            )
        return chat

    @classmethod
    def startwith(cls, name: str = '', /, *, query: bool = False) -> Union[BaseQuery, list[Chat]]:
        """
        Get all chats whose title startwith `name`.
        Since private chats has title of None, they are not included.

        Args:
            name (str, optional): start of the title. Defaults to ''.
            query (bool, optional): to return as `sqlalchemy.BaseQuery`. Defaults to False.

        Returns:
            Union[flask_sqlalchemy.BaseQuery, list[Chat]]
        """
        chats = cls.query.filter(
            cls.title.startswith(name)
        )
        if not query:
            chats = chats.all()
        return chats

    def __repr__(self) -> str:
        return self.__class__.__name__ + (
            f"(id={self.id}, kind={self.kind.name})"
        )


class Message(db.Model, ModelMixin):
    """
    Model representing message.

    Arguments:
        chat (Chat): chat which message belongs to
        from_user (User): sender user
        is_service (bool, optionsl), defaults to False.
        text (str): message text
        reply_to (Message): message which this message is reply to
        created_at (datetime, optional), defaults to `datetime.utcnow()`
        edited_at (datetime, optional), defaults to None
    """
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, ForeignKey('user.id'))
    chat_id = Column(
        Integer, ForeignKey('chat.id', ondelete="CASCADE")
    )
    is_service = Column(Boolean, nullable=False, default=False)
    reply_to_id = Column(
        Integer, ForeignKey('message.id', ondelete="SET NULL")
    )
    text = Column(String(4096), nullable=False)
    created_at = Column(
        DateTime(), default=dt.utcnow
    )
    edited_at = Column(
        DateTime(), onupdate=dt.utcnow,
        nullable=True, default=None
    )

    from_user = relationship(
        'User', uselist=False, foreign_keys=[from_user_id]
    )
    seen_by = relationship(
        'User', secondary=message_view, lazy='dynamic',
        passive_deletes=True,
    )
    reply_to = relationship('Message', remote_side=[id])

    @validates('seen_by', include_removes=True)
    def validate_view(self, key: str, user: User, is_remove: bool) -> User:
        """
        Validate view addition. Fires on every view addition or removal.

        Args:
            key (str): 'seen_by'
            user (User): user to add the view from
            is_remove (bool): whether this call is for removal

        Raises:
            ValueError: is_remove is True
            ValueError: user is not member of message's chat

        Returns:
            User: user that was validate. Same user as the one passed in.
        """
        # pylint: disable=unused-argument
        if is_remove:
            raise ValueError('not allowed to remove view')
        if user not in self.chat.members:
            raise ValueError('cannot add view by non-member user')
        return user

    @hybrid_method
    def add_view(self, user: User) -> True:
        """
        Add view to the message by user.

        Args:
            user (User): user to add the view from

        Returns:
            True
        """
        self.seen_by.append(user)
        return True

    def __repr__(self) -> str:
        return self.__class__.__name__ + (
            f"(id={self.id}, chat={self.chat!r}, from_user={self.from_user!r})"
        )
