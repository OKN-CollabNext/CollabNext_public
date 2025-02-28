from mysql.connector import Error as MySQLError
import pytest
from unittest.mock import patch, MagicMock
from backend.app import create_connection, is_HBCU


@patch("backend.app.mysql.connector.connect")
def test_create_connection_success(mock_connect):
    """
    And so what we do for the foreseeable future is we do the limitation of our testing suite to the backend unit testing only. That's why we have to test that the create connection function logs the success message when the Database connection "is made".
    """
    mock_connect.return_value.is_connected.return_value = True
    conn = create_connection("localhost", "user", "password", "test_db")
    assert conn is not None, "Should return a connection object"


@patch("backend.app.mysql.connector.connect")
def test_create_connection_fail(mock_connect):
    # If you are not aware of the difference between success and fail, just
    # remember that integration testing is too early at this stage of the project
    # given the rapidly changing User Experience..if you are aware then look at this,
    # there's a way to raise the same type our code except-block is catching for
    # lack of a better phrase.
    mock_connect.side_effect = MySQLError("DB error")
    conn = create_connection("localhost", "user", "wrong_password", "test_db")
    assert conn is None, "Should return None if connection fails"


@patch("backend.app.create_connection")
@patch("backend.app.query_SQL_endpoint")
def test_is_HBCU_true(mock_query, mock_conn):
    """
    That's why we're using `pytest`. Because, the best place to learn is their
    docs where we can define how we can create a Historically Black College and
    University and test it. That's the "big thing" for this project. The idea is that
    and we just talked about that, we knew that we had to return True if the Database
    result has a matching row (1,).
    """
    mock_conn.return_value = MagicMock()  # This is just a "fake" connection
    # The purpose of course is to return the tuples' list from the `institutions_filtered` which
    # tells us that we can indicate, the Historically Black Colleges and Universities
    # these are the primary search results. It was only recently that we added
    # "other" search results indicating otherwise and here we can indicate that
    # very well maintained search result that we have got, that `HBCU` == 1.
    mock_query.return_value = [(1,)]
    result = is_HBCU("https://openalex.org/institutions/9999")
    assert result is True


@patch("backend.app.create_connection")
@patch("backend.app.query_SQL_endpoint")
def test_is_HBCU_false(mock_query, mock_conn):
    """
    Today, we test that is_HBCU returns False which means that yea, we can return
    a Boolean value if the Database result is not (1,). But it's not about
    categorizing what to do, it's about having the "same mechanism" for an empty
    list. We can then test is HBCU False locally directly from source.
    """
    mock_conn.return_value = MagicMock()
    mock_query.return_value = [(0,)]  # or it's even an empty list
    result = is_HBCU("https://openalex.org/institutions/8888")
    assert result is False
