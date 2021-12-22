from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from shmelegram.models import Chat, User, Message


class ChatSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Chat
        exclude = ['kind']
        include_fk = True
        include_relationships = True


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True


class MessageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        include_fk = False
        include_relationships = True
