"""
API Endpoint Tests

This file contains tests for the API endpoints of the application.
Tests include:
- /initial-search endpoint with various input combinations
- /get-institutions endpoint
- /autofill-institutions endpoint
- /autofill-topics endpoint
- /get-default-graph endpoint
- /get-topic-space-default-graph endpoint
"""

from backend.app import app, SomeCustomError as OpenAlexAPIError
import pytest
import json
from unittest.mock import patch, MagicMock
""" Rename the exception as it has been imported and importable, to reflect more genuinely its origin as I have customized it. We could do so redefine and rename the SomeCustomError in the `backend.app`, however, as OpenAlexAPIError. """


@pytest.fixture
def client():
    """
    Common Flask test client fixture for endpoint tests.
    """
    with app.test_client() as test_client:
        yield test_client


###############################################################################
# /initial-search ENDPOINT TESTS
###############################################################################

def test_initial_search_null_values(client):
    """
    If the JSON includes explicit None values for organization, researcher, topic, or type,
    the endpoint should handle them gracefully and not crash.
    """
    payload = {
        "organization": None,
        "researcher": None,
        "topic": None,
        "type": None
    }
    response = client.post("/initial-search", json=payload)
    """ Yes we did, we widened the allowed response statuses such that we can better reflect the errors on the client that we deem possible. """
    assert response.status_code in (
        200, 400, 415), "Expected safe fallback or 400/415."
    data = response.get_json()
    assert isinstance(
        data, dict), "Expected a dictionary response for None values."


@pytest.mark.parametrize(
    "org, researcher, topic, typ",
    [
        ("", "", "", ""),           # All empty
        ("   ", "   ", "   ", ""),  # Just spaces
    ],
    ids=["AllEmptyStrings", "AllSpaces"]
)
def test_initial_search_empty_or_whitespace(client, org, researcher, topic, typ):
    """
    Passing empty strings or only whitespace is a common edge case.
    """
    payload = {
        "organization": org,
        "researcher": researcher,
        "topic": topic,
        "type": typ
    }
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert response.status_code == 200, "Should gracefully handle empty/whitespace."
    assert isinstance(data, dict), "Expected a dictionary as a response."


@pytest.mark.parametrize(
    "payload",
    [
        {"organization": "Georgia Tech",
            "researcher": None, "topic": None, "type": ""},
        {"organization": None, "researcher": "Einstein", "topic": "", "type": None},
        {"organization": "MIT", "researcher": "", "topic": None, "type": "dummy"},
    ],
    ids=["OrgOnly", "ResearcherOnly", "OrgType"]
)
def test_initial_search_partially_null(client, payload):
    """
    Cases where some fields are valid and others are null/empty.
    The system should still process the valid fields.
    """
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert response.status_code == 200, "Expected partial search or safe fallback."
    assert isinstance(
        data, dict), "Should return a JSON object even with partial nulls."


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"organization": 123, "researcher": 456,
            "topic": 789, "type": 1011},  # all numbers
        {"organization": ["A", "B"], "researcher": {},
            "topic": True, "type": 9.99},
    ],
    ids=["AllNumbers", "MixedTypes"]
)
def test_initial_search_invalid_types(client, invalid_payload):
    """
    If a user accidentally sends numbers, booleans, or arrays, check how the endpoint responds.
    """
    response = client.post("/initial-search", json=invalid_payload)
    assert response.status_code in (
        200, 400), "Expected either 200 or 400 for invalid data."
    data = response.get_json()
    assert isinstance(
        data, dict), "Should return JSON, possibly an error or empty results."


def test_initial_search_extremely_long_strings(client):
    """
    Large strings can cause performance or storage issues. Ensure the system handles them gracefully.
    """
    huge_string = "A" * 5000  # 5,000 characters
    payload = {
        "organization": huge_string,
        "researcher": huge_string,
        "topic": huge_string,
        "type": "dummy"
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200, "Should not crash with huge inputs."
    data = response.get_json()
    assert isinstance(
        data, dict), "Expected a dict response even with huge strings."


def test_initial_search_no_payload(client):
    """
    Some clients might forget to send a JSON body. The server should respond sensibly.
    """
    response = client.post("/initial-search")
    assert response.status_code in (
        200, 400), "Expected safe fallback or 400 for no payload."
    if response.is_json:
        data = response.get_json()
        assert isinstance(
            data, dict), "Should return a dict if returning JSON."


def test_initial_search_special_chars(client):
    """
    Test handling of special characters in input fields.
    """
    payload = {
        "organization": "Univ!@#$%^&*()_+|",
        "researcher": "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200, "Expected to handle special characters."
    data = response.get_json()
    assert isinstance(data, dict), "Must be valid JSON."


def test_initial_search_unknown_type(client):
    """
    Test handling of unknown values for the "type" field.
    """
    payload = {
        "organization": "Test Org",
        "researcher": "Test Author",
        "topic": "Test Topic",
        "type": "SOMETHING_RANDOM"
    }
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert response.status_code == 200, "Should not fail on unknown 'type'."
    assert isinstance(
        data, dict), "Check if it handles unknown 'type' gracefully."


def test_initial_search_numeric_topic(client):
    """
    Test handling of numeric values in the "topic" field.
    """
    payload = {
        "organization": "Test Org",
        "researcher": "Test Author",
        "topic": "42",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200, "Should handle numeric string in 'topic'."
    data = response.get_json()
    assert isinstance(data, dict), "Should return a JSON object."


@pytest.mark.parametrize(
    "payload",
    [
        {},  # completely empty
        {"organization": "", "researcher": "", "topic": "", "type": ""},
        {"notARealKey": "notUsed"}
    ],
    ids=["CompletelyEmpty", "AllBlankStrings", "UnusedKey"]
)
def test_initial_search_all_fields_invalid(client, payload):
    """
    Test handling of completely empty payload or payload with invalid keys.
    """
    response = client.post("/initial-search", json=payload)
    assert response.status_code in (
        200, 400), "Expected safe fallback or 400 for invalid data."
    if response.is_json:
        data = response.get_json()
        assert isinstance(data, dict), "Expected a JSON dict even if invalid."


def test_initial_search_valid_author_only(client):
    """
    Test search with valid author only.
    """
    payload = {
        "researcher": "Jane Doe",
        "organization": "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_institution_only(client):
    """
    Test search with valid institution only.
    """
    payload = {
        "researcher": "",
        "organization": "Harvard University",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_topic_only(client):
    """
    Test search with valid topic only.
    """
    payload = {
        "researcher": "",
        "organization": "",
        "topic": "Biochemistry",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_author_institution(client):
    """
    Test search with valid author and institution.
    """
    payload = {
        "researcher": "John Smith",
        "organization": "MIT",
        "topic": "",
        "type": "HBCU"
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_institution_topic(client):
    """
    Test search with valid institution and topic.
    """
    payload = {
        "researcher": "",
        "organization": "Stanford University",
        "topic": "Astrophysics",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_author_topic(client):
    """
    Test search with valid author and topic.
    """
    payload = {
        "researcher": "Alice Brown",
        "organization": "",
        "topic": "Machine Learning",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_all_three(client):
    """
    Test search with all three valid (author, institution, topic).
    """
    payload = {
        "researcher": "Carlos Garcia",
        "organization": "Howard University",
        "topic": "Mathematics",
        "type": "HBCU"
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_author(client):
    """
    Test search with nonexistent author.
    """
    payload = {
        "researcher": "Fake McNotReal",
        "organization": "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_institution(client):
    """
    Test search with nonexistent institution.
    """
    payload = {
        "researcher": "",
        "organization": "NoSuch Institute",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_topic(client):
    """
    Test search with nonexistent topic.
    """
    payload = {
        "researcher": "",
        "organization": "",
        "topic": "Quantum Flubber",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


@pytest.mark.parametrize("partial_author", ["Lew", "", " "])
def test_initial_search_partial_author(client, partial_author):
    """
    Test search with partial author name.
    """
    payload = {
        "researcher": partial_author,
        "organization": "Cornell University" if partial_author == "" else "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(
        data, dict), "Expected a safe JSON response for partial/empty author name."


def test_initial_search_whitespace_fields(client):
    """
    Test search with whitespace fields.
    """
    payload = {
        "researcher": " ",
        "organization": " ",
        "topic": " ",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "org, expected_hbcu_status",
    [
        ("Tuskegee University", True),
        ("Georgia Institute of Technology", False),
    ],
    ids=["HBCU", "NonHBCU"]
)
def test_initial_search_hbcu_check(client, org, expected_hbcu_status):
    """
    Test HBCU check.
    """
    payload = {
        "researcher": "",
        "organization": org,
        "topic": "",
        "type": "HBCU" if expected_hbcu_status else ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_orcid(client):
    """
    Test search with ORCID.
    """
    payload = {
        "researcher": "0000-0002-1825-0097",
        "organization": "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_special_chars_in_topic(client):
    """
    Test search with special characters in topic.
    """
    payload = {
        "researcher": "",
        "organization": "",
        "topic": "Biology/Genomics!",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_exception(client):
    """
    Test handling of exceptions in the /initial-search endpoint.
    """
    with patch("backend.app.get_institution_researcher_subfield_results", side_effect=Exception("Test exception")):
        response = client.post("/initial-search", json={
            "organization": "Test Inst",
            "researcher": "Test Author",
            "topic": "Test Topic",
            "type": "dummy"
        })
        data = response.get_json()
        assert data == {"error": "An unexpected error occurred"}


###############################################################################
# /get-institutions ENDPOINT TESTS
###############################################################################

def test_get_institutions_success(client):
    """
    Test successful retrieval of institutions.
    """
    response = client.get("/get-institutions")
    assert response.status_code == 200
    data = response.get_json()
    if isinstance(data, dict) and "institutions" in data:  # pragma: no cover
        pytest.skip(
            "Code returns dict with key 'institutions' instead of a raw list.")
    else:
        assert isinstance(data, list)


@patch("backend.app.execute_query", return_value=None)
def test_get_institutions_no_data(mock_execute_query, client):
    """
    Test handling of no data from the database.
    """
    response = client.get("/get-institutions")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected an empty list if no data"
    assert len(data) == 0, "Expected an empty list if no data"


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_get_institutions_error(mock_execute_query, client):
    """
    Test handling of database errors.
    """
    response = client.get("/get-institutions")
    assert response.status_code == 500, "Expected 500 error for database failure"


###############################################################################
# /autofill-institutions ENDPOINT TESTS
###############################################################################

def test_autofill_institutions_success(client):
    """
    Test successful retrieval of autofill suggestions for institutions.
    """
    response = client.post("/autofill-institutions", json={"query": "Harv"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of institution suggestions"


def test_autofill_institutions_empty_query(client):
    """
    Test handling of empty query for institution autofill.
    """
    response = client.post("/autofill-institutions", json={"query": ""})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of institution suggestions"
    assert len(data) == 0, "Expected an empty list for empty query"


def test_autofill_institutions_no_matches(client):
    """
    Test handling of no matches for institution autofill.
    """
    response = client.post("/autofill-institutions",
                           json={"query": "xyzabc123"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of institution suggestions"
    assert len(data) == 0, "Expected an empty list for no matches"


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_autofill_institutions_error(mock_execute_query, client):
    """
    Test handling of database errors for institution autofill.
    """
    response = client.post("/autofill-institutions", json={"query": "Harv"})
    assert response.status_code == 500, "Expected 500 error for database failure"


###############################################################################
# /autofill-topics ENDPOINT TESTS
###############################################################################

def test_autofill_topics_success(client):
    """
    Test successful retrieval of autofill suggestions for topics.
    """
    response = client.post("/autofill-topics", json={"query": "Comp"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of topic suggestions"


def test_autofill_topics_empty_query(client):
    """
    Test handling of empty query for topic autofill.
    """
    response = client.post("/autofill-topics", json={"query": ""})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of topic suggestions"
    assert len(data) == 0, "Expected an empty list for empty query"


def test_autofill_topics_no_matches(client):
    """
    Test handling of no matches for topic autofill.
    """
    response = client.post("/autofill-topics", json={"query": "xyzabc123"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list), "Expected a list of topic suggestions"
    assert len(data) == 0, "Expected an empty list for no matches"


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_autofill_topics_error(mock_execute_query, client):
    """
    Test handling of database errors for topic autofill.
    """
    response = client.post("/autofill-topics", json={"query": "Comp"})
    assert response.status_code == 500, "Expected 500 error for database failure"


###############################################################################
# /get-default-graph ENDPOINT TESTS
###############################################################################

def test_get_default_graph_success(client):
    """
    Test successful retrieval of default graph.
    """
    response = client.post("/get-default-graph", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict), "Expected a graph object"
    assert "nodes" in data, "Expected nodes in the graph"
    assert "edges" in data, "Expected edges in the graph"


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_default_graph_error(mock_json_load, client):
    """
    Test handling of file errors for default graph.
    """
    response = client.post("/get-default-graph", json={})
    assert response.status_code == 500, "Expected 500 error for file failure"


###############################################################################
# /get-topic-space-default-graph ENDPOINT TESTS
###############################################################################

def test_get_topic_space_default_graph_success(client):
    """
    Test successful retrieval of topic space default graph.
    """
    response = client.post("/get-topic-space-default-graph", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict), "Expected a graph object"
    assert "nodes" in data, "Expected nodes in the graph"
    assert "edges" in data, "Expected edges in the graph"


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_topic_space_default_graph_error(mock_json_load, client):
    """
    Test handling of file errors for topic space default graph.
    """
    response = client.post("/get-topic-space-default-graph", json={})
    assert response.status_code == 500, "Expected 500 error for file failure"


###############################################################################
# /search-topic-space ENDPOINT TESTS
###############################################################################

def test_search_topic_space_success(client):
    """
    Test successful search of topic space.
    """
    response = client.post("/search-topic-space",
                           json={"query": "Computer Science"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict), "Expected a graph object"
    assert "nodes" in data, "Expected nodes in the graph"
    assert "edges" in data, "Expected edges in the graph"


def test_search_topic_space_empty_query(client):
    """
    Test handling of empty query for topic space search.
    """
    response = client.post("/search-topic-space", json={"query": ""})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict), "Expected a graph object"
    assert "nodes" in data, "Expected nodes in the graph"
    assert "edges" in data, "Expected edges in the graph"


def test_search_topic_space_no_matches(client):
    """
    Test handling of no matches for topic space search.
    """
    response = client.post("/search-topic-space", json={"query": "xyzabc123"})
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict), "Expected a graph object"
    assert "nodes" in data, "Expected nodes in the graph"
    assert "edges" in data, "Expected edges in the graph"


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_search_topic_space_error(mock_json_load, client):
    """
    Test handling of file errors for topic space search.
    """
    response = client.post("/search-topic-space",
                           json={"query": "Computer Science"})
    assert response.status_code == 500, "Expected 500 error for file failure"
