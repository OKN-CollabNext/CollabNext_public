"""
Merged Data Tests: test_endpoints.py

Consolidates:
  1) test_postgres_models.py
  2) test_models.py
  3) test_sparql.py

into a single file for data-related testing.

Sections:
  A) REAL POSTGRES INTEGRATION TESTS
  B) MOCK-BASED DATABASE UTILS TESTS
  C) MOCK-BASED SPARQL TESTS
"""

from backend.app import create_connection, is_HBCU  # direct import is fine here
import pytest
import psycopg2
from psycopg2.errors import UndefinedTable
from unittest.mock import patch, MagicMock
import requests

###############################################################################
# FIXTURES
###############################################################################


@pytest.fixture(scope="module")
def pg_connection():
    """
    Provides a real Postgres connection for DB tests.
    Modify host/user/password/dbname to match your local or CI environment.
    """
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="secret",
        dbname="my_test_db",
    )
    yield conn
    conn.close()


@pytest.fixture
def pg_cursor(pg_connection):
    """
    Creates a fresh cursor before each test; rolls back after the test.
    """
    cur = pg_connection.cursor()
    try:
        yield cur
    finally:
        pg_connection.rollback()


###############################################################################
# SECTION A: REAL POSTGRES INTEGRATION TESTS
###############################################################################

def test_create_temp_table(pg_cursor):
    """
    Simple example: create a TEMP table, insert data, read it back.
    """
    # Create a TEMP table
    pg_cursor.execute("""
        CREATE TEMP TABLE test_users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL
        );
    """)

    # Insert some rows
    pg_cursor.execute(
        "INSERT INTO test_users (username) VALUES (%s), (%s) RETURNING id;",
        ("alice", "bob")
    )
    inserted_ids = pg_cursor.fetchall()
    assert len(inserted_ids) == 2, "Should have inserted 2 rows"

    # Query them back
    pg_cursor.execute("SELECT username FROM test_users ORDER BY id;")
    rows = pg_cursor.fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "alice"
    assert rows[1][0] == "bob"


def test_missing_table(pg_cursor):
    """
    Example that demonstrates handling an exception when table doesn't exist.
    """
    with pytest.raises(UndefinedTable):
        pg_cursor.execute("SELECT * FROM non_existent_table;")


###############################################################################
# SECTION B: MOCK-BASED DATABASE UTILS TESTS (from test_models.py)
###############################################################################


@patch("backend.app.psycopg2.connect")
@pytest.mark.parametrize(
    "connection_closed, expected_conn",
    [
        (0, True),
        (1, False),
    ],
    ids=["ConnOpen", "ConnClosed"]
)
def test_create_connection_success(mock_connect, connection_closed, expected_conn):
    """
    If psycopg2.connect returns a connection and .closed == 0, it's open; else closed or invalid.
    """
    mock_conn = MagicMock()
    mock_conn.closed = connection_closed
    mock_connect.return_value = mock_conn

    conn = create_connection(
        host="fake_host",
        user="fake_user",
        password="fake_pass",
        dbname="fake_db"
    )
    if expected_conn:
        assert conn is not None, "Expected a valid connection object"
    else:
        assert conn is None, "Expected None if connection is closed"


@patch("backend.app.psycopg2.connect", side_effect=Exception("Generic PG error"))
def test_create_connection_fail(mock_connect):
    """
    If psycopg2.connect(...) raises an exception, create_connection should return None.
    """
    conn = create_connection(
        host="fake_host",
        user="fake_user",
        password="wrong_pass",
        dbname="fake_db"
    )
    assert conn is None, "Should return None if psycopg2.connect fails."


@pytest.mark.parametrize(
    "db_result, expected_bool",
    [
        ([(1,)], True),
        ([(0,)], False),
        ([], False),
    ],
    ids=["HBCU_True", "HBCU_False_Zero", "HBCU_NoResult"]
)
@patch("backend.app.execute_query")
def test_is_HBCU(mock_execute, db_result, expected_bool):
    """
    Checks that is_HBCU(...) returns True if the DB query indicates HBCU (1), False otherwise.
    """
    mock_execute.return_value = db_result
    result = is_HBCU("https://openalex.org/institutions/9999")
    assert result == expected_bool, f"Expected {expected_bool}, got {result}"


@patch("backend.app.psycopg2.connect")
def test_execute_query_success(mock_connect):
    """
    Mocks a successful psycopg2 connection & query execution for execute_query(...).
    """
    from backend import app as app_module  # local import to avoid conflicts

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("result",)]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    result = app_module.execute_query("SELECT 1", ())
    assert result == [("result",)]
    mock_cursor.execute.assert_called_once()


@patch("backend.app.psycopg2.connect", side_effect=Exception("DB error"))
def test_execute_query_failure(mock_connect):
    """
    If connect() raises Exception, execute_query(...) returns None.
    """
    from backend import app as app_module
    result = app_module.execute_query("SELECT 1", ())
    assert result is None


@patch("backend.app.execute_query")
def test_get_author_ids_found(mock_exec):
    """
    Checks that get_author_ids(...) properly parses a DB row with 'author_id'.
    """
    from backend import app as app_module
    mock_exec.return_value = [[{"author_id": "id_001"}]]
    result = app_module.get_author_ids("Some Author")
    assert result == {"author_id": "id_001"}


@patch("backend.app.execute_query")
def test_get_author_ids_not_found(mock_exec):
    """
    If DB returns None or empty, we get None from get_author_ids(...).
    """
    from backend import app as app_module
    mock_exec.return_value = None
    result = app_module.get_author_ids("Unknown Author")
    assert result is None


@patch("backend.app.execute_query")
def test_get_institution_id_found(mock_exec):
    """
    Checks that get_institution_id(...) returns the 'institution_id' from the row.
    """
    from backend import app as app_module
    mock_exec.return_value = [[{"institution_id": 1234}]]
    result = app_module.get_institution_id("Some Institution")
    assert result == 1234


@patch("backend.app.execute_query")
def test_get_institution_id_empty_dict(mock_exec):
    """
    If DB row is empty or missing 'institution_id', returns None.
    """
    from backend import app as app_module
    mock_exec.return_value = [[{}]]
    result = app_module.get_institution_id("Some Institution")
    assert result is None


###############################################################################
# SECTION C: MOCK-BASED SPARQL TESTS (from test_sparql.py)
###############################################################################

@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_success_data_tests(mock_post):
    """
    Mocks a successful SPARQL endpoint POST request.
    Potentially can be extended for real SPARQL tests if you have a live endpoint.
    """
    from backend import app as app_module
    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "results": {
            "bindings": [
                {"var1": {"value": "val1"}, "var2": {"value": "val2"}}
            ]
        }
    }
    mock_post.return_value = fake_response

    result = app_module.query_SPARQL_endpoint("http://example.com", "SELECT *")
    assert isinstance(result, list)
    assert result == [{"var1": "val1", "var2": "val2"}]


@patch("backend.app.requests.post", side_effect=requests.exceptions.RequestException("Error"))
def test_query_SPARQL_endpoint_failure_data_tests(mock_post):
    """
    If the POST fails, query_SPARQL_endpoint(...) returns empty list.
    """
    from backend import app as app_module
    result = app_module.query_SPARQL_endpoint("http://example.com", "SELECT *")
    assert result == []


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_institution_metadata_sparql_no_results_data_tests(mock_query):
    """
    get_institution_metadata_sparql(...) returns {} if no SPARQL results.
    """
    from backend import app as app_module
    result = app_module.get_institution_metadata_sparql("Nonexistent")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_metadata_sparql_valid_data_tests(mock_query):
    """
    Checks that we parse institution fields from a valid SPARQL response.
    """
    from backend import app as app_module
    mock_query.return_value = [{
        "ror": "ror123",
        "workscount": "100",
        "citedcount": "200",
        "homepage": "http://homepage",
        "institution": "semopenalex/institution/abc",
        "peoplecount": "50"
    }]
    result = app_module.get_institution_metadata_sparql("Test Institution")
    assert result["ror"] == "ror123"
    assert result["works_count"] == "100"
    assert result["homepage"] == "http://homepage"
    assert "openalex" in result["oa_link"]


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_author_metadata_sparql_no_results_data_tests(mock_query):
    """
    get_author_metadata_sparql(...) returns {} if no SPARQL results.
    """
    from backend import app as app_module
    result = app_module.get_author_metadata_sparql("Nonexistent Author")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_author_metadata_sparql_valid_data_tests(mock_query):
    """
    Checks that we parse author fields from a valid SPARQL response.
    """
    from backend import app as app_module
    mock_query.return_value = [{
        "cite_count": "300",
        "orcid": "orcid123",
        "works_count": "50",
        "current_institution_name": "Test Univ",
        "author": "semopenalex/author/xyz",
        "current_institution": "semopenalex/institution/inst"
    }]
    result = app_module.get_author_metadata_sparql("Test Author")
    assert result["cited_by_count"] == "300"
    assert result["orcid"] == "orcid123"
    assert "openalex" in result["oa_link"]
