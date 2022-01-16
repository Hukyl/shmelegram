"""
This module introduces schema for converting sqlalchemy models to json dicts
Defines following classes:
    - `ChatSchema`
    - `UserSchema`
    - `MessageSchema`
"""

# pylint: disable=too-few-public-methods

from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from shmelegram.models import Chat, User, Message

class ChatSchema(SQLAlchemyAutoSchema):
    """Schema for chat json dumping"""

    class Meta:
        """Chat schema metadata"""
        model = Chat
        exclude = ['kind']
        include_fk = True
        include_relationships = True

    type = fields.Method('get_kind')

    def get_kind(self, chat: Chat):
        """
        Get type of chat.

        Args:
            chat (Chat)

        Returns:
            str: string name of enum entry
        """
        return chat.kind.name.lower()


class UserSchema(SQLAlchemyAutoSchema):
    """Schema for user json dumping"""

    class Meta:
        """User schema metadata"""
        model = User
        include_fk = True


class MessageSchema(SQLAlchemyAutoSchema):
    """Schema for message json dumping"""

    class Meta:
        """Message schema metadata"""
        model = Message
        include_fk = False
        include_relationships = True
