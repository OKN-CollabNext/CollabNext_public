import os
import pytest
import requests
import json
from unittest.mock import patch, MagicMock

from backend import app as app_module


@patch("backend.app.psycopg2.connect")
def test_execute_query_success(mock_connect):
    """ First, we want to set up a fake connection & cursor that returns the result "that we know". We are following the guidelines from Lew and the mock queries provided by Dean in order to integrate our database with these mock tests so that we can not only test whether the database is even responding but we can also test the functions offline we can test the functions by mocking and simulating the database actions with key-value pairs that are identical in terms of data structure. """
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
    result = app_module.execute_query("SELECT 1", ())
    assert result is None


@patch("backend.app.requests.get")
def test_fetch_last_known_institutions_success(mock_get):
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {
        "last_known_institutions": [
            {"display_name": "Test Univ",
             "id": "https://openalex.org/mockInstitutionId"}
        ]
    }
    mock_get.return_value = response_mock
    result = app_module.fetch_last_known_institutions(
        "https://openalex.org/author/abc")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["display_name"] == "Test Univ"


@patch("backend.app.requests.get")
def test_fetch_last_known_institutions_http_error(mock_get):
    response_mock = MagicMock()
    response_mock.status_code = 404
    response_mock.json.return_value = {}
    mock_get.return_value = response_mock
    with pytest.raises(app_module.SomeCustomError):
        app_module.fetch_last_known_institutions(
            "https://openalex.org/author/abc")


@patch("backend.app.execute_query")
def test_get_author_ids_found(mock_exec):
    """ I have to simulate a database response that returns a list with a dictionary. The ultimate goal of course is to merge database integration into main. In order todo that we need to complete the Azure testing where we test if a container that has been created using Docker is Azure workable "in the sense" that Azure can interact with that container properly. """
    mock_exec.return_value = [[{"author_id": "id_001"}]]
    result = app_module.get_author_ids("Some Author")
    """ "Know" that get_author_ids returns results[0][0] so the expected value is a dictionary.  """
    assert result == {"author_id": "id_001"}


@patch("backend.app.execute_query")
def test_get_author_ids_not_found(mock_exec):
    mock_exec.return_value = None
    result = app_module.get_author_ids("Unknown Author")
    assert result is None


@patch("backend.app.execute_query")
def test_get_institution_id_found(mock_exec):
    mock_exec.return_value = [[{"institution_id": 1234}]]
    result = app_module.get_institution_id("Some Institution")
    assert result == 1234


@patch("backend.app.execute_query")
def test_get_institution_id_empty_dict(mock_exec):
    mock_exec.return_value = [[{}]]
    result = app_module.get_institution_id("Some Institution")
    assert result is None


@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_success(mock_post):
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
def test_query_SPARQL_endpoint_failure(mock_post):
    result = app_module.query_SPARQL_endpoint("http://example.com", "SELECT *")
    assert result == []


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_institution_metadata_sparql_no_results(mock_query):
    result = app_module.get_institution_metadata_sparql("Nonexistent")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_metadata_sparql_valid(mock_query):
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
def test_get_author_metadata_sparql_no_results(mock_query):
    result = app_module.get_author_metadata_sparql("Nonexistent Author")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_author_metadata_sparql_valid(mock_query):
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


@patch("backend.app.query_SQL_endpoint", return_value=[(1,)])
@patch("backend.app.create_connection")
def test_is_HBCU_true(mock_create, mock_query):
    result = app_module.is_HBCU("https://openalex.org/institutions/123")
    assert result is True


@patch("backend.app.query_SQL_endpoint", return_value=[(0,)])
@patch("backend.app.create_connection")
def test_is_HBCU_false(mock_create, mock_query):
    result = app_module.is_HBCU("https://openalex.org/institutions/456")
    assert result is False


@patch("backend.app.query_SQL_endpoint", return_value=[])
@patch("backend.app.create_connection")
def test_is_HBCU_no_result(mock_create, mock_query):
    result = app_module.is_HBCU("https://openalex.org/institutions/789")
    assert result is False
