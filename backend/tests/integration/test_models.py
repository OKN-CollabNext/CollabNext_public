""" And so what we do for the foreseeable future is we do limit the testing suite to the backend unit tests only..that is the reason that we have to test that the create connection function logs the success message WHEN the database connection "is made". """
from mysql.connector import Error as MySQLError
import pytest
from unittest.mock import patch, MagicMock
from backend.app import create_connection, is_HBCU


@pytest.mark.integration
@pytest.mark.parametrize(
    "mock_is_connected, expected_conn",
    [
        (True, True),
        (False, True),
    ],
    ids=["DBConnectSuccess", "DBConnectSuccessButNotConnected"]
)
@patch("backend.app.mysql.connector.connect")
def test_create_connection_success(mock_connect, mock_is_connected, expected_conn):
    """
    I was fully satisfied by the creation of a connection; if you are not aware of the difference between success and fail, you need only remember that integration testing is too early at this stage of the project. Given the rapidly changing User Experience Design...if you are aware then look at this: there is a way to raise the same type that our code except-block is catching, for lack of a better phrase. However, we aren't going to need to do that because "THIS" function is designed to parameterically test the create_connection success_like scenarios.
    """
    mock_connect.return_value.is_connected.return_value = mock_is_connected
    conn = create_connection("localhost", "user", "password", "test_db")
    if expected_conn:
        assert conn is not None, "Should return a connection object"
    else:
        assert conn is None, "Should return None"


@pytest.mark.integration
@pytest.mark.parametrize(
    "side_effect, expected_conn",
    [
        (MySQLError("DB error"), None),
        (Exception("Generic error"), None),
    ],
    ids=["MySQLError", "GenericException"]
)
@patch("backend.app.mysql.connector.connect")
def test_create_connection_fail(mock_connect, side_effect, expected_conn):
    """
    Furthermore, we can parameterically test for when the create_connection is failing to connect.
    """
    mock_connect.side_effect = side_effect
    conn = create_connection("localhost", "user", "wrong_password", "test_db")
    assert conn == expected_conn, f"Expected {expected_conn}, got {conn}"


@pytest.mark.integration
@pytest.mark.parametrize(
    "institution_url, db_result, expected_bool",
    [
        ("https://openalex.org/institutions/9999", [(1,)], True),
        ("https://openalex.org/institutions/8888", [(0,)], False),
        ("https://openalex.org/institutions/7777", [], False),
    ],
    ids=["HBCU_True", "HBCU_False_Zero", "HBCU_NoResult"]
)
@patch("backend.app.create_connection")
@patch("backend.app.query_SQL_endpoint")
def test_is_HBCU(mock_query, mock_conn, institution_url, db_result, expected_bool):
    """
    We know, that's why we're using `pytest`. Because the best place to learn is their docs where we can define how we can create a Historically Black College and University and test it. That's the primary goal for this project. The big idea is that and we just talked about that we knew, that we had to return True if the Database result has a matching row (1,). Therefore we can parameterically test for is_HBCU with multiple institution IDs. We can "pass" these as parameters and then make fake connections.
    """
    mock_conn.return_value = MagicMock()
    """ This is just a "fake" connection. The purpose of course is to return the tuples' list from the `institutions_filtered` which tells us that yes, we can indicate Historically Black Colleges and Universities these are the primary search results, it was only recently that we added "other' search results indicating otherwise and here now we can indicate that very well maintained search result that we have got, when `HBCU` == 1.  """
    mock_query.return_value = db_result
    """ Today, we test that is_HBCU returns False which means that yea, we can return a Boolean value if the Database result is not (1,). But it's not about categorizing what to do, it's about having the "same mechanism" for an empty list. We can then test is_HBCU False? We can test that locally directly from the source EVEN if it's an empty list.  """
    result = is_HBCU(institution_url)
    assert result == expected_bool, f"For {institution_url}, expected {expected_bool}, got {result}"
