import pytest


@pytest.fixture
def client():
    from shmelegram import app, db
    from shmelegram.models import Chat, Message, User

    with app.test_client() as client:
        with app.app_context():
            db.init_app(app)
        yield client


@pytest.fixture
def db():
    from shmelegram import db
    from shmelegram.models import Chat, Message, User

    db.create_all()
    db.session = db.create_scoped_session()
    yield db
    db.drop_all()


@pytest.fixture
def user():
    from shmelegram.models import User

    return User(username='username', password='pa$$Word123')