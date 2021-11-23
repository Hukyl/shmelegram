from __future__ import annotations
from hashlib import sha256

from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from shmelegram import db
from shmelegram.config import ChatKind


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
        return sha256(value.encode('utf-8')).hexdigest()


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    from_user = relationship('User', uselist=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    is_service = db.Column(db.Boolean, nullable=False, default=False)
    text = db.Column(db.String(4096), nullable=False)
    datetime = db.Column(
        db.DateTime(), server_default=func.current_timestamp()
    )


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Enum(ChatKind))
    title = db.Column(db.String(50), nullable=True)
    members = relationship('User', secondary=chat_membership, backref='chats')
    messages = relationship(
        'Message', lazy='dynamic', backref='chat',
        cascade="all, delete-orphan", passive_deletes=True        
    )

    def __init__(self, *, kind: ChatKind, title: str = None):
        if kind is ChatKind.PRIVATE and title:
            raise ValueError('unable to set title in private chat')
        elif kind is not ChatKind.PRIVATE and not title:
            raise ValueError('unable to create non-private chat without title')
        super().__init__(kind=kind, title=title)

    @hybrid_property
    def member_limit(self) -> int:
        return self.kind.value

    @hybrid_property
    def member_count(self) -> int:
        return db.object_session(self).query(User).with_parent(self).count()

    @hybrid_method
    def add_member(self, user: User) -> True:
        member_limit = self.member_limit
        if self.member_count >= member_limit:
            raise ValueError(
                f'member count exceeds member limit ({member_limit})'
            )
        self.members.append(user)
        return True

    @hybrid_method
    def add_message(self, message: Message) -> True:
        self.messages.append(message)
        return True
