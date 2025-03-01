import os
import pytest
from backend.app import create_connection
""" This thing about the configuration test file is that we can't change the frontend just yet. Doing extra creation of connections is fine but there is always more to be done in any project. That's why it's so important to ask ourselves do we test the higher-level wrapper OR do we test whatever the (search and so on) functions return? That's a rhetorical question. """


@pytest.fixture(scope="session")
def db_connection():
    """
    Here is a sample fixture for a database connection IF it is necessary for testing integration. You can provide arguments that are real arguments or mock dummy arguments as needed.
    This will be created once per pytest session and it will be used again, "speeding up" tests that share the identical database connection.
    """
    conn = create_connection("fake_host", "fake_user", "fake_pass", "fake_db")
    yield conn
    if conn:
        conn.close()


@pytest.fixture
def db_cursor(db_connection):
    """
    Working in our own branch we created a function-scoped fixture; obtain a fresh cursor from the session-level db_connection for each test.
    """
    cursor = db_connection.cursor() if db_connection else None
    yield cursor
    if cursor:
        cursor.close()


def pytest_collection_modifyitems(config, items):
    """
    For the explanatory text, we have some items that rely on environment variables. We want to auto-skip tests that are marked as 'integration' IF the environment variable skip_DB =true.
    """
    if os.getenv("SKIP_DB", "false").lower() == "true":
        skip_integration = pytest.mark.skip(
            reason="SKIP_DB=true: skipping integration tests."
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
