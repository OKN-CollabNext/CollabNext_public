from datetime import datetime
import psycopg2
import sys
import pytest
# Here's our new import. I have no April Fool's jokes today. There's enough craziness going on that we don't need to make fun of anything else.
from backend.app import app
import os
os.chdir(os.path.join(os.path.dirname(__file__), '..'))
_test_outcomes = []
_test_finish_message = []
# Easy button, that's the foundation of our tool's simplicity and usefulness. Well,
# that's why we're checking the logs and debugging, the project root directory to `sys.path` for when the app "fails" and goes broke.
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '.')))


@pytest.fixture(autouse=True, scope='session')
def set_working_directory():
    # That's what we do, in the pre-beta version, change the current
    # working directory to the backend folder. I finally re-set the `cwd`.
    # The expectation is that `conftest.py` is in `backend/tests/conftest.py`.
    backend_dir = os.path.join(os.path.dirname(__file__), '..')
    os.chdir(backend_dir)
    print("Changed working directory to:", os.getcwd())


@pytest.fixture(scope='session', autouse=True)
def set_base_dir():
    # Not to be too urgent but and however this..I don't know how else
    # to put it but this sets the BASE_DIR correctly for all types of tests.
    # When the BASE_DIR broke, it's like Jekyll; they're defined in some obscure
    # place like `package.json` in Azure.
    from backend import app
    app.BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="module")
def pg_connection():
    """
    If you want a single Postgres connection for DB tests, do it here.
    Adjust host/user/password/dbname for your environment. But it really depends on which database setup fixture you want to go, from coverage to indicate external dependency. We're not going to try to bite that whole thing off as a major Artificial Intelligence integration with the database because, that's out of scope of the original project.
    """
    conn = None
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
    when SKIP_DB=true, you can adjust logic here as needed according to the pagination OR you can look at the topics, resources, institution name, and modify the items in a more concise and succinct format.
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
    (actual test run), ignoring "setup" or "teardown". I tried asking ChatGPT
    the difference between skip(s) and fail(s) and success(es), but I could not.
    Because, the answers were pretty poor and "mere" coverage of the report does
    not preclude test "success or failure".
    """
    outcome = yield
    result = outcome.get_result()
    if result.when == "call":
        _test_outcomes.append((item.nodeid, result.outcome))


def pytest_sessionfinish(session, exitstatus):
    """
    Store the ..pytest session finish message (in)directly for reporting. Called after the entire test run completes. We write our collected
    test outcomes to a timestamped text file, e.g. "20250305_145045_test_run.txt".
    """
    # Build onto a timestamped filename like 20250305_145045_test_run.txt.
    # If you wanna find out which tests are responsible for the coverage,
    # you would think it's easy, but it's not.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_test_run.txt"
    with open(filename, "w") as f:
        f.write("==== Pytest Results ====\n\n")
        for nodeid, outcome in _test_outcomes:
            f.write(f"{nodeid} -> {outcome}\n")
        f.write("\n==== Pytest Exit Status ====\n")
        f.write(f"Exit Code: {exitstatus}\n")
    # Instead of trying to append to the hook function, we store our message in a list for better results; it's a simple yet effective way to present data, however if you want to see the full picture you have to run `pytest` or `python -m pytest` from the `./CollabNext_public/backend`, directory. It's a lighthearted nod to the Boolean "versioning" of the test "results".
    _test_finish_message.append(f"Test results saved to: {filename}")


def pytest_report_header(config):
    """
    This hook returns the additional line "dumps" that appear in the pytest report header. While we "can't" exclude the `autofill_topics_list` from not being..
    rendered, we can report each test case; consider it a short demo or presentation
    on the `pytest` coverage "full" report on the tool.
    """
    return _test_finish_message if _test_finish_message else []


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
