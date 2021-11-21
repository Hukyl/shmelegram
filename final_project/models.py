from __future__ import annotations
from enum import Enum
from hashlib import sha256

from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy.schema import CheckConstraint, PrimaryKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from final_project import db


class ChatKind(Enum):
    """
    Enumeration of chat types.
    The value of chat type is the max number of members
        the chat can hold.
    
    Attributes:
        GROUP (int): group chat type
        PRIVATE (int): private chat type
    """

    PRIVATE = 2
    GROUP = 50


chat_membership = db.Table(
    'chat_membership', db.Model.metadata,
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)

    __table_args__ = (
        CheckConstraint(
            'char_length(username) > 4', name='username_min_length'
        ), 
    )

    @validates('username')
    def validate_username(self, key: str, value: str) -> str:
        if len(value) <= 4:
            raise ValueError('username too short')
        return value

    @validates('password')
    def validate_password(self, key: str, value: str) -> str:
        if not (6 < len(value) < 15):
            raise ValueError('invalid password length')
        return sha256(value).hexdigest()


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer)
    from_user = relationship('User', uselist=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    is_service = db.Column(db.Boolean, nullable=False, default=False)
    text = db.Column(db.String(4096), nullable=True)
    datetime = db.Column(db.DateTime(), server_default=func.utcnow())

    __table_args__ = (
        PrimaryKeyConstraint('id', 'chat_id', name='chat_message_pk'),
    )


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Enum(ChatKind))
    _member_limit = db.Column(db.Integer)
    title = db.Column(db.String(50), nullable=True)
    members = relationship(
        'User', secondary=chat_membership, lazy='subquery', 
        backref=db.backref('chats', lazy=True)
    )
    messages = relationship(
        'Message', lazy='dynamic', backref='chat',
        cascade="all, delete-orphan", passive_deletes=True        
    )

    def __init__(
                self, kind: ChatKind, *, title: str = None, 
                members: list[User] = None
            ):
        if kind is ChatKind.PRIVATE and title:
            raise ValueError('unable to set title in private chat')
        elif kind is not ChatKind.PRIVATE and not title:
            raise ValueError('unable to create non-private chat without title')
        self.kind = kind
        self.title = title
        if not members:
            members = []
        self.members = []

    @hybrid_property
    def member_limit(self) -> int:
        return self._member_limit

    @hybrid_property
    def member_count(self) -> int:
        return db.object_session(self).query(User).with_parent(self).count()

    @hybrid_method
    def add_member(self, user: User) -> True:
        member_limit = self.member_limit
        if self.members_count >= member_limit:
            raise ValueError(
                f'member count exceeds member limit ({member_limit})'
            )
        self.members.append(user)
        return True
