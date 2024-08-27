import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db import Base


@pytest.fixture(scope='function')
def test_session():
    """Returns an SQLAlchemy session, and after the test tears down everything properly."""
    # Use an in-memory SQLite database for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    # Drop all tables after tests complete
    Base.metadata.drop_all(engine)

    session.close()
    transaction.rollback()
    connection.close()
    