"""
External Services Tests

This file contains tests for external service interactions in the application.
Tests include:
- OpenAlex API interactions
- SPARQL endpoint queries
- Error handling for external service failures
- Fallback mechanisms when services are unavailable
"""

from backend.app import (
    app,
    fetch_last_known_institutions,
    SomeCustomError as OpenAlexAPIError,
    query_SPARQL_endpoint,
    get_institution_metadata_sparql,
    get_author_metadata_sparql,
    get_topic_and_researcher_metadata_sparql,
    get_institution_and_topic_metadata_sparql,
    get_institution_and_topic_and_researcher_metadata_sparql,
)
import pytest
import requests
import responses
from unittest.mock import patch, MagicMock
""" And so on and so forth, the imported exception I rename for internal consistency all across the unit tests. """

# Use the actual SPARQL endpoint URL from the application
SPARQL_ENDPOINT = "https://semopenalex.org/sparql"


###############################################################################
# OPENALEX API TESTS
###############################################################################

def test_fetch_institutions_handles_http_error(requests_mock):
    """
    Confirm that a non-200 status code triggers OpenAlexAPIError when fetching from OpenAlex.
    """
    requests_mock.get("https://api.openalex.org/authors/999", status_code=500)
    with pytest.raises(OpenAlexAPIError):
        fetch_last_known_institutions("https://openalex.org/author/999")


@pytest.mark.parametrize(
    "status_code, expected_result",
    [
        (200, [{"display_name": "Test University"}]),
        (404, OpenAlexAPIError),
        (500, OpenAlexAPIError),
    ],
    ids=["Success", "NotFound", "ServerError"]
)
def test_fetch_institutions_status_codes(requests_mock, status_code, expected_result):
    """
    Test handling of different HTTP status codes in fetch_last_known_institutions.
    """
    author_id = "12345"
    url = f"https://api.openalex.org/authors/{author_id}"

    if status_code == 200:
        requests_mock.get(url, json={"last_known_institutions": [
                          {"display_name": "Test University"}]}, status_code=status_code)
        result = fetch_last_known_institutions(
            f"https://openalex.org/author/{author_id}")
        assert result == expected_result
    else:
        requests_mock.get(url, status_code=status_code)
        with pytest.raises(expected_result):
            fetch_last_known_institutions(
                f"https://openalex.org/author/{author_id}")


@responses.activate
def test_fetch_institutions_responses_multiple():
    """
    Test handling multiple mocked HTTP calls to OpenAlex API.
    """
    # Mock a successful 200 response
    responses.add(
        responses.GET,
        "https://api.openalex.org/authors/555",
        json={"last_known_institutions": [{"display_name": "Resp Univ"}]},
        status=200,
    )
    # Mock a 404 response for a different author
    responses.add(
        responses.GET,
        "https://api.openalex.org/authors/666",
        json={"detail": "Not Found"},
        status=404,
    )

    institutions_200 = fetch_last_known_institutions(
        "https://openalex.org/author/555")
    assert len(institutions_200) == 1
    assert institutions_200[0]["display_name"] == "Resp Univ"

    # This should raise OpenAlexAPIError
    with pytest.raises(OpenAlexAPIError):
        fetch_last_known_institutions("https://openalex.org/author/666")


def test_fetch_institutions_malformed_id():
    """
    Test that malformed OpenAlex IDs are handled properly.
    """
    with pytest.raises(OpenAlexAPIError):
        fetch_last_known_institutions("not-a-valid-openalex-url")

    with pytest.raises(OpenAlexAPIError):
        fetch_last_known_institutions(
            "https://openalex.org/author/not-a-number")


###############################################################################
# SPARQL ENDPOINT TESTS
###############################################################################

@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_success(mock_post):
    """
    Test successful SPARQL endpoint query with mocked response.
    """
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

    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert isinstance(result, list)
    assert result == [{"var1": "val1", "var2": "val2"}]


@patch("backend.app.requests.post", side_effect=requests.exceptions.RequestException("Error"))
def test_query_SPARQL_endpoint_failure(mock_post):
    """
    Test SPARQL endpoint query failure with mocked exception.
    """
    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert result == []


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_institution_metadata_sparql_no_results(mock_query):
    """
    Test get_institution_metadata_sparql returns empty dict when no results.
    """
    result = get_institution_metadata_sparql("Nonexistent")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_metadata_sparql_valid(mock_query):
    """
    Test parsing institution fields from a valid SPARQL response.
    """
    mock_query.return_value = [{
        "ror": "ror123",
        "workscount": "100",
        "citedcount": "200",
        "homepage": "http://homepage",
        "institution": "semopenalex/institution/abc",
        "peoplecount": "50"
    }]
    result = get_institution_metadata_sparql("Test Institution")
    assert result["ror"] == "ror123"
    assert result["works_count"] == "100"
    assert result["homepage"] == "http://homepage"
    assert "openalex" in result["oa_link"]


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_author_metadata_sparql_no_results(mock_query):
    """
    Test get_author_metadata_sparql returns empty dict when no results.
    """
    result = get_author_metadata_sparql("Nonexistent Author")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_author_metadata_sparql_valid(mock_query):
    """
    Test parsing author fields from a valid SPARQL response.
    """
    mock_query.return_value = [{
        "cite_count": "300",
        "orcid": "orcid123",
        "works_count": "50",
        "current_institution_name": "Test Univ",
        "author": "semopenalex/author/xyz",
        "current_institution": "semopenalex/institution/inst"
    }]
    result = get_author_metadata_sparql("Test Author")
    assert result["cited_by_count"] == "300"
    assert result["orcid"] == "orcid123"
    assert "openalex" in result["oa_link"]


###############################################################################
# COMBINED METADATA TESTS
###############################################################################

@patch("backend.app.query_SPARQL_endpoint")
def test_get_topic_and_researcher_metadata_sparql(mock_query):
    """
    Test retrieving combined topic and researcher metadata from SPARQL.
    """
    mock_query.return_value = [{
        "author": "semopenalex/author/123",
        "orcid": "0000-0001-2345-6789",
        "works_count": "25",
        "cite_count": "150",
        "current_institution_name": "Test University",
        "current_institution": "semopenalex/institution/456",
        "topic": "semopenalex/topic/789"
    }]

    result = get_topic_and_researcher_metadata_sparql(
        "Machine Learning", "John Doe")

    assert "researcher_oa_link" in result
    assert "topic_oa_link" in result
    assert "orcid" in result
    assert "work_count" in result
    assert "cited_by_count" in result
    assert "current_institution" in result


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_and_topic_metadata_sparql(mock_query):
    """
    Test retrieving combined institution and topic metadata from SPARQL.
    """
    mock_query.return_value = [{
        "institution": "semopenalex/institution/123",
        "ror": "https://ror.org/12345",
        "homepage": "https://university.edu",
        "topic": "semopenalex/topic/456"
    }]

    result = get_institution_and_topic_metadata_sparql(
        "Test University", "Computer Science")

    assert "institution_oa_link" in result
    assert "topic_oa_link" in result
    assert "ror" in result
    assert "homepage" in result


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_and_topic_and_researcher_metadata_sparql(mock_query):
    """
    Test retrieving combined institution, topic, and researcher metadata from SPARQL.
    """
    mock_query.return_value = [{
        "institution": "semopenalex/institution/123",
        "ror": "https://ror.org/12345",
        "author": "semopenalex/author/456",
        "orcid": "0000-0001-2345-6789",
        "topic": "semopenalex/topic/789"
    }]

    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Test University", "Computer Science", "John Doe"
    )

    assert "institution_oa_link" in result
    assert "topic_oa_link" in result
    assert "researcher_oa_link" in result
    assert "ror" in result
    assert "orcid" in result


###############################################################################
# ERROR HANDLING TESTS
###############################################################################

@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_malformed_response(mock_post):
    """
    Test handling of malformed SPARQL response.
    """
    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    # Missing the expected structure
    fake_response.json.return_value = {"unexpected": "format"}
    mock_post.return_value = fake_response

    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert result == []


@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_empty_bindings(mock_post):
    """
    Test handling of empty bindings in SPARQL response.
    """
    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {
        "results": {
            "bindings": []
        }
    }
    mock_post.return_value = fake_response

    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert result == []


@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_json_decode_error(mock_post):
    """
    Test handling of JSON decode error in SPARQL response.
    """
    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.side_effect = ValueError("Invalid JSON")
    mock_post.return_value = fake_response

    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert result == []
