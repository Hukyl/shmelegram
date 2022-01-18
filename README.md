# Shmelegram
Shmelegram is a web Telegram-like messenger.

It was originally built for EPAM Python Autumn 2021 Course as a final project.


## How to build this app

- ### Navigate to the project root folder

- ### Optionally set up and activate the virtual environment:
```
virtualenv venv
source env/bin/activate
```

- ### Install the requirements:
```
pip install .
```
- ### Configure MySQL database and Redis server

- ### Set the following environment variables:

```
MYSQL_USER=<your_mysql_user>
MYSQL_PASSWORD=<your_mysql_user_password>
MYSQL_SERVER=<your_mysql_server>
MYSQL_DATABASE=<your_mysql_database_name>
REDIS_USER=<your_redis_user>
REDIS_PASSWORD=<your_redis_user_password>
REDIS_HOST=<your_redis_host>
REDIS_PORT=<your_redis_port>
FLASK_TESTING=<True for testing, False for production usage>
```

*You can set these in .env file as the project uses dotenv module to load 
environment variables*

- ### Run migrations to create database infrastructure:
```
flask db upgrade
```

- ### Run the project locally:
```
python -m flask run
```

## Now you should be able to access the web service and web application on the following addresses:

- ### Web Application:
```
localhost:5000/home
localhost:5000/home/about

localhost:5000/auth/register
localhost:5000/auth/login
localhost:5000/auth/logout

localhost:5000/
```


- ### Web Service
```
localhost:5000/api/chats
localhost:5000/api/chats/<chat_id>

localhost:5000/api/messages/<message_id>
localhost:5000/api/messages/chat/<chat_id>

localhost:5000/api/users
localhost:5000/api/users/<user_id>
localhost:5000/api/users/<user_id>/chats
localhost:5000/api/users/<user_id>/chats/<chat_id>/unread
```