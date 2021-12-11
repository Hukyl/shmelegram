from __future__ import annotations
from hashlib import sha256

from sqlalchemy.sql import func
from sqlalchemy.orm import validates, relationship
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from shmelegram import db
from shmelegram.config import ChatKind
from shmelegram import utils


chat_membership = db.Table(
    'chat_membership', db.Model.metadata,
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id', ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"))
)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    last_online = db.Column(
        db.DateTime(), server_default=func.now(), 
        nullable=True, onupdate=func.current_timestamp()
    )  # None means online now

    __table_args__ = (
        CheckConstraint(
            'length(username) > 4', name='username_min_length'
        ), 
    )

    @hybrid_method
    def check_password(self, password: str) -> bool:
        return sha256(password.encode('utf-8')).hexdigest() == self.password

    @validates('username')
    def validate_username(self, key: str, value: str) -> str:
        if not utils.validate_username(value):
            raise ValueError('invalid username length')
        return value

    @validates('password')
    def validate_password(self, key: str, value: str) -> str:
        if not utils.validate_password(value):
            raise ValueError('invalid password length')
        return sha256(value.encode('utf-8')).hexdigest()


class Chat(db.Model):
    __tablename__ = 'chat'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.Enum(ChatKind))
    title = db.Column(db.String(50), nullable=True)
    members = relationship(
        'User', secondary=chat_membership, backref='chats', 
        passive_deletes=True
    )
    messages = relationship(
        'Message', lazy='dynamic', backref='chat',
        cascade="all, delete", passive_deletes=True        
    )

    def __init__(self, *, kind: ChatKind, title: str = None):
        if kind is ChatKind.PRIVATE and title:
            raise ValueError('unable to set title in private chat')
        elif kind is ChatKind.GROUP and not title:
            raise ValueError('unable to create non-private chat without title')
        super().__init__(kind=kind, title=title)

    @hybrid_property
    def member_limit(self) -> int:
        return self.kind.value

    @hybrid_property
    def member_count(self) -> int:
        return User.query.with_parent(self).count()

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

    def __str__(self) -> str:
        return f"Chat(kind={self.kind.name})"


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    from_user = relationship('User', uselist=False, foreign_keys=[from_user_id])
    chat_id = db.Column(
        db.Integer, db.ForeignKey('chat.id', ondelete="CASCADE")
    )
    is_service = db.Column(db.Boolean, nullable=False, default=False)
    seen_user_ids = db.Column(db.Integer, db.ForeignKey('user.id'))
    seen_by = relationship('User', uselist=True, foreign_keys=[seen_user_ids])
    text = db.Column(db.String(4096), nullable=False)
    created_at = db.Column(
        db.DateTime(), server_default=func.current_timestamp()
    )

    @hybrid_method
    def add_view(self, user: User) -> True:
        if user not in self.chat.members:
            raise ValueError('cannot add view by non-member user')
        self.seen_by.append(user)
        return True
