from dotenv import load_dotenv
load_dotenv()

import os


user = os.environ.get('MYSQL_USER')
password = os.environ.get('MYSQL_PASSWORD')
server = os.environ.get('MYSQL_SERVER')
database = os.environ.get('MYSQL_DATABASE')


class Config:
    DEBUG = True
    SECRET_KEY = os.urandom(32)
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqlconnector://{user}:{password}' \
                              f'@{server}/{database}'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
