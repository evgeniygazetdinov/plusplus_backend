import uuid

import pytest

from chat_volc.models.models import ChatAlreadyExistsError, Message, PrivateChat, User
from chat_volc.models.schemas import PrivateChatCreate


def test_user_repr():
    user = User(uid="test-uid", username="alice")

    assert repr(user) == "<User(uid='test-uid', username='alice', email='None')>"


def test_private_chat_create_chat(db_session, two_users):
    user_one, user_two = two_users

    chat = PrivateChat.create_chat(db_session, user_one.id, user_two.id)

    assert chat.id is not None
    assert chat.user_one_id == user_one.id
    assert chat.user_two_id == user_two.id


def test_private_chat_create_chat_reverse_order_conflict(db_session, two_users):
    user_one, user_two = two_users
    first = PrivateChat.create_chat(db_session, user_one.id, user_two.id)

    with pytest.raises(ChatAlreadyExistsError) as exc_info:
        PrivateChat.create_chat(db_session, user_two.id, user_one.id)

    assert exc_info.value.chat.id == first.id
    assert str(exc_info.value) == "Chat already exists between these two users."


def test_message_create_message(db_session, chat):
    private_chat, user_one, _ = chat
    data = type("Data", (), {"user_id": user_one.uid, "text": "hello"})()

    message = Message.create_message(db_session, private_chat.id, data)

    assert message.id is not None
    assert message.text == "hello"
    assert message.user_id == user_one.id
    assert message.chat_id == private_chat.id


def test_message_create_message_user_not_in_chat(db_session, chat, make_user):
    private_chat, _, _ = chat
    outsider = make_user("outsider")
    data = type("Data", (), {"user_id": outsider.uid, "text": "hello"})()

    with pytest.raises(Exception, match="chat or user id not exists"):
        Message.create_message(db_session, private_chat.id, data)


def test_message_create_message_chat_not_found(db_session, make_user):
    user = make_user("solo")
    data = type("Data", (), {"user_id": user.uid, "text": "hello"})()

    with pytest.raises(Exception, match="chat or user id not exists"):
        Message.create_message(db_session, 9999, data)


def test_private_chat_create_schema():
    schema = PrivateChatCreate(
        user_one_uid=str(uuid.uuid4()),
        user_two_uid=str(uuid.uuid4()),
    )

    assert schema.user_one_uid
    assert schema.user_two_uid
