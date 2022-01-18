"""
This module contains config data for project
Defines following classes:
    - `BaseConfig`, base class for config classes
    - `Config`, production config
    - `TestConfig`, testing config
    - `ChatKind`, chat kinds enumeration
"""

# pylint: disable=too-few-public-methods

from os import getenv, urandom
from enum import IntEnum

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base config class"""

    DEBUG = True
    MIGRATION_DIR = 'shmelegram/migrations'
    TESTING = getenv('FLASK_TESTING', '').strip() == 'True'
    SECRET_KEY = urandom(32)
    API_RESPONSE_SIZE = 50
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class Config(BaseConfig):
    """Production config class"""

    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{}:{}@{}/{}'.format(
        getenv('MYSQL_USER'), getenv('MYSQL_PASSWORD'),
        getenv('MYSQL_SERVER'), getenv('MYSQL_DATABASE')
    )
    REDIS_URL = 'redis://{}:{}@{}:{}/{}'.format(
        getenv('REDIS_USER'), getenv('REDIS_PASSWORD'),
        getenv('REDIS_HOST'), getenv('REDIS_PORT'),
        int(getenv('REDIS_DATABASE_NUMBER', '0'))
    )
    REDIS_MESSAGE_QUEUE_URL = 'redis://{}:{}@{}:{}/{}'.format(
        getenv('REDIS_USER'), getenv('REDIS_PASSWORD'),
        getenv('REDIS_HOST'), getenv('REDIS_PORT'),
        int(getenv('REDIS_MESSAGE_QUEUE_DATABASE_NUMBER', '1'))
    )


class TestConfig(BaseConfig):
    """Testing config class"""

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    REDIS_URL = 'redis://@localhost:6379/0'
    REDIS_MESSAGE_QUEUE_URL = 'redis://@localhost:6379/1'



class ChatKind(IntEnum):
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
