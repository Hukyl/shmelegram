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
- ### Configure MySQL database

- ### Set the following environment variables:

```
MYSQL_USER=<your_mysql_user>
MYSQL_PASSWORD=<your_mysql_user_password>
MYSQL_SERVER=<your_mysql_server>
MYSQL_DATABASE=<your_mysql_database_name>
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

localhost:5000/
```
