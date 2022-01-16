"""
This packet introduces REST API classes.
Defines following classes:
    - `user/UserBaseApi`
    - `user/UserListApi`
    - `user/UserApi`
    - `user/UserChatListApi`
    - `user/UnreadMessagesUserChatApi`
    - `chat/ChatBaseApi`
    - `chat/ChatApi`
    - `chat/ChatListApi`
    - `message/MessageBaseApi`
    - `message/MessageApi`
    - `message/ChatMessagesApi`
"""

from typing import Any, NewType

from flask import Blueprint


JsonDict = dict[str, Any]
StatusCode = NewType('StatusCode', int)

bp = Blueprint('api', __name__, url_prefix='/api')
