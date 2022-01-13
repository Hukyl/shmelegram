from __future__ import annotations

from datetime import datetime as dt
from hashlib import sha256
from typing import Any, List, NoReturn, Optional, TypeVar, Type

from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import backref, load_only, relationship, validates
from sqlalchemy.schema import CheckConstraint

from shmelegram import db, utils
from shmelegram.config import ChatKind

T = TypeVar('T', bound='ModelMixin')
ModelId = TypeVar('ModelId')
JsonDict = dict[str, Any]


chat_membership = db.Table(
    'chat_membership', db.Model.metadata,
    db.Column(
        'chat_id', db.Integer, db.ForeignKey('chat.id', ondelete="CASCADE")
    ),
    db.Column(
        'user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")
    )
)

message_view = db.Table(
    'message_view', db.Model.metadata, 
    db.Column(
        'user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")
    ), 
    db.Column(
        'message_id', db.Integer, 
        db.ForeignKey('message.id', ondelete="CASCADE")
    )
)


class ModelMixin:
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
        for k, v in data.items():
            setattr(self, k, v)
        db.session.add(self)

    @classmethod
    def get(cls: Type[T], id_: ModelId) -> T:
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
    def get_or_none(cls: Type[T], id_: ModelId) -> Optional[T]:        
        """
        Get model by some id. If this id does not exist, return None

        Args:
            id_ (int): id of model to be retrieved

        Returns:
            db.Model: model
        """
        return cls.query.get(id_)

    def delete(self):
        db.session.delete(self)
        db.session.flush()

    def save(self):
        db.session.add(self)
        db.session.flush()


class User(db.Model, ModelMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    last_online = db.Column(
        db.DateTime(), default=dt.utcnow, 
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
        self.last_online = dt.utcnow()
        db.session.add(self)

    @classmethod
    def get_by_username(cls, username: str, /) -> bool:
        user = cls.query.filter(cls.username == username).first()
        if user is None:
            raise ValueError(
                f"{cls.__name__} with username {username!r} does not exist"
            )
        return user

    @classmethod
    def username_exists(cls, username: str, /) -> bool:
        return db.session.query(User.id).filter_by(
                username=username).first() is not None

    @classmethod
    def startwith(cls, name: str = '', /, *, query: bool = False) -> bool:
        users = cls.query.filter(
            cls.username.startswith(name)
        )
        if not query:
            users = users.all()
        return users

    @hybrid_method
    def check_password(self, password: str) -> bool:
        return sha256(password.encode('utf-8')).hexdigest() == self.password

    @validates('username')
    def validate_username(self, key: str, value: str) -> str:
        if not utils.validate_username(value):
            raise ValueError('invalid username')
        return value

    @validates('password')
    def validate_password(self, key: str, value: str) -> str:
        if not utils.validate_password(value):
            raise ValueError('invalid password')
        return sha256(value.encode('utf-8')).hexdigest()


class Chat(db.Model, ModelMixin):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Enum(ChatKind))
    title = db.Column(db.String(50), nullable=True)

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
    def validate_member(self, key: str, user: User):
        member_limit = self.member_limit
        if self.member_count >= member_limit:
            raise ValueError(
                f'member count exceeds member limit ({member_limit})'
            )
        return user

    @hybrid_property
    def member_limit(self) -> int:
        return self.kind.value

    @hybrid_property
    def member_count(self) -> int:
        return len(self.members)

    def add_member(self, user: User) -> True:
        self.members.append(user)
        return True

    def remove_member(self, user: User) -> True:
        self.members.remove(user)
        return True

    def get_unread_messages(self, user: User) -> List[Message]:
        """
        Get unread messages by a user.
        If user not a member of a chat, raise ValueError

        Args:
            user (User): user to be checked

        Returns:
            List[Message]
        """
        if user not in self.members:
            raise ValueError('cannot get messages by non-member user')
        return self.messages.filter(~Message.seen_by.any(User.id == user.id))\
            .options(load_only("id")).all()

    def get_private_title(self, user: User) -> str:
        if self.kind is not ChatKind.PRIVATE:
            raise ValueError("cannot get private title of non-private chat")
        members = list(self.members)
        if user not in members:
            raise ValueError('cannot get title for non-member user')
        members.remove(user)
        return members[0].username

    @classmethod
    def get_by_title(cls, title: str, /) -> bool:
        chat = cls.query.filter(cls.title == title).first()
        if chat is None:
            raise ValueError(
                f'{cls.__name__} with title {title!r} does not exist'
            )
        return chat

    @classmethod
    def startwith(cls, name: str = '', /, *, query: bool = False) -> bool:
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
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    chat_id = db.Column(
        db.Integer, db.ForeignKey('chat.id', ondelete="CASCADE")
    )
    is_service = db.Column(db.Boolean, nullable=False, default=False)
    reply_to_id = db.Column(
        db.Integer, db.ForeignKey('message.id', ondelete="SET NULL")
    )
    text = db.Column(db.String(4096), nullable=False)
    created_at = db.Column(
        db.DateTime(), default=dt.utcnow
    )
    edited_at = db.Column(
        db.DateTime(), onupdate=dt.utcnow,
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
    def validate_view(self, key: str, user: User, is_remove: bool):
        if is_remove:
            raise ValueError('not allowed to remove view')
        elif user not in self.chat.members:
            raise ValueError('cannot add view by non-member user')
        return user

    @hybrid_method
    def add_view(self, user: User) -> True:
        self.seen_by.append(user)
        return True

    def __repr__(self) -> str:
        return self.__class__.__name__ + (
            f"(id={self.id}, chat={self.chat!r}, from_user={self.from_user!r})"
        )
