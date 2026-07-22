from chat_volc.settings import get_db


def test_get_db_yields_session(db_session):
    generator = get_db()
    session = next(generator)

    assert session is not None

    generator.close()
