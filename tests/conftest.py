import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from chat_volc.models.models import Message, PrivateChat, User  # noqa: F401
from chat_volc.settings import Base, get_db
from main import app


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    def _make_user(username: str = "test_user") -> User:
        user = User(uid=str(uuid.uuid4()), username=username)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def two_users(make_user):
    return make_user("alice"), make_user("bob")


@pytest.fixture
def chat(db_session, two_users):
    user_one, user_two = two_users
    private_chat = PrivateChat.create_chat(db_session, user_one.id, user_two.id)
    return private_chat, user_one, user_two
