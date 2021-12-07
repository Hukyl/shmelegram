from enum import Enum

from dotenv import load_dotenv


load_dotenv()
os = __import__("os")


user = os.environ.get('MYSQL_USER')
password = os.environ.get('MYSQL_PASSWORD')
server = os.environ.get('MYSQL_SERVER')
database = os.environ.get('MYSQL_DATABASE')

MIGRATION_DIR = 'shmelegram/migrations'
TESTING = os.environ.get('FLASK_TESTING', '').strip() == 'True'


class Config:
    DEBUG = True
    SECRET_KEY = os.urandom(32)
    if TESTING:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    else:
        SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{user}:{password}' \
                                f'@{server}/{database}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


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
