# conftest.py

import os
import pytest
import psycopg2
from datetime import datetime

_test_outcomes = []


@pytest.fixture(scope="module")
def pg_connection():
    """
    If you want a single Postgres connection for DB tests, do it here.
    Adjust host/user/password/dbname for your environment.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME"),
            sslmode='disable',
        )
        yield conn
    except psycopg2.Error as e:
        pytest.fail(f"Database connection error: {e}")
    finally:
        if conn:
            conn.close()


@pytest.fixture
def pg_cursor(pg_connection):
    cur = pg_connection.cursor()
    try:
        yield cur
    finally:
        pg_connection.rollback()


def pytest_collection_modifyitems(config, items):
    """
    We no longer have any separate integration tests, so there's no need
    for an 'integration' marker. If you still want to skip DB tests
    when SKIP_DB=true, you can adjust logic here as needed.
    """
    if os.getenv("SKIP_DB", "false").lower() == "true":
        skip_db = pytest.mark.skip(
            reason="SKIP_DB=true: skipping DB-related tests."
        )
        for item in items:
            if "db" in item.keywords:
                item.add_marker(skip_db)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook into each phase of a test call. We only look at the "call" phase
    (actual test run), ignoring "setup" or "teardown".
    """
    outcome = yield
    result = outcome.get_result()
    if result.when == "call":
        _test_outcomes.append((item.nodeid, result.outcome))


def pytest_sessionfinish(session, exitstatus):
    """
    Called after the entire test run completes. We write our collected
    test outcomes to a timestamped text file, e.g. "20250305_145045_test_run.txt".
    """

    # Build a timestamped filename like 20250305_145045_test_run.txt
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_test_run.txt"

    # If you want to avoid overwriting an existing file, you can check here:
    # if os.path.exists(filename):
    #     # handle naming collision, e.g., add a random suffix

    with open(filename, "w") as f:
        f.write("==== Pytest Results ====\n\n")
        for nodeid, outcome in _test_outcomes:
            f.write(f"{nodeid} -> {outcome}\n")

        f.write("\n==== Pytest Exit Status ====\n")
        f.write(f"Exit Code: {exitstatus}\n")

    session.config.hook.pytest_report_header.append(f"Test results saved to: {filename}")
