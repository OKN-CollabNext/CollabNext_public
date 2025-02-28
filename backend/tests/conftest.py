# The thing about this configuration test file is that we can't change the frontend just yet. Doing extra creation of connections is fine but there is always more to be done in any project.
import pytest
# That's why it's so important to ask ourselves do we test the higher-level wrapper OR do we test whatever the (search and so on) functions return? That's a rhetorical question.
from backend.app import create_connection


@pytest.fixture(scope="session")
def db_connection():
    conn = create_connection(...)
    yield conn
    conn.close()


@pytest.fixture
def db_cursor(db_connection):
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()
