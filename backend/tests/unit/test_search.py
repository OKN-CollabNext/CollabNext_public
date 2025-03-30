"""
Search Tests

This file contains tests for the search functionality of the application.
Tests include:
- Edge cases for /initial-search endpoint
- Search function unit tests with mocked database calls
- Parameter validation and error handling
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app import (
    app,
    initial_search,
    search_by_author,
    search_by_author_institution_topic,
    search_by_author_institution,
    search_by_institution_topic,
    search_by_author_topic,
    search_by_topic,
    search_by_institution,
)
import json


@pytest.fixture
def client():
    """
    Common Flask test client fixture for endpoint tests.
    """
    with app.test_client() as test_client:
        yield test_client
###############################################################################
# EDGE CASES FOR /initial-search
###############################################################################


def test_initial_search_null_values(client):
    """
    If the JSON includes explicit None values for organization, researcher, topic, or type,
    the endpoint should handle them gracefully and not crash.
    """
    payload = {"organization": None,
               "researcher": None, "topic": None, "type": None}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert isinstance(data, dict)


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
    assert response.status_code in (
        200, 500), "Expected partial search or 500 fallback."
    if data is None:
        pytest.fail("No JSON returned; skipping partial null test.")
    if not isinstance(data, dict):
        pytest.fail(f"Expected dict, got {type(data)}; skipping.")


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
        200, 400, 500), "Expected 200 or 400 or 500 for invalid data."
    data = response.get_json()
    if data is None:
        pytest.fail("Got None for invalid types; skipping.")
    if not isinstance(data, dict):
        pytest.fail(f"Expected dict, got {type(data)}; skipping.")


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
        200, 400, 415, 500), "Expected safe fallback or 400/415/500 for no payload."
    if response.is_json:
        data = response.get_json()
        assert isinstance(
            data, dict), "Should return a dict if returning JSON."


def test_initial_search_special_chars(client):
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
    response = client.post("/initial-search", json=payload)
    assert response.status_code in (
        200, 400, 500), "Expected safe fallback or 400 or 500 for invalid data."
    if response.is_json:
        data = response.get_json()
        assert isinstance(data, dict), "Expected a JSON dict even if invalid."


###############################################################################
# SEARCH FUNCTION TESTS
###############################################################################

@pytest.mark.parametrize(
    "author_name, get_author_ids_result, search_by_author_result, final_expected",
    [
        (
            "Lew Lefton",
            [[{"author_id": "1234"}]],
            [
                {
                    "author_metadata": {
                        "orcid": None,
                        "openalex_url": "https://openalex.org/author/1234",
                        "last_known_institution": "Test University--FRINK",
                        "num_of_works": 10,
                        "num_of_citations": 100
                    },
                    "data": [
                        {"topic": "Physics", "num_of_works": 5},
                        {"topic": "Math",    "num_of_works": 3}
                    ]
                }
            ],
            True,
        ),
        (
            "Empty Author",
            None,
            None,
            False,
        )
    ],
    ids=["AuthorFound", "AuthorNotFound"]
)
@patch("backend.app.execute_query")
def test_search_by_author_param(
    mock_exec, author_name, get_author_ids_result, search_by_author_result, final_expected
):
    """
    Testing search_by_author(...) with different database return scenarios (mocked).
    """
    if get_author_ids_result is None:
        mock_exec.side_effect = [None]
    else:
        mock_exec.side_effect = [
            [(get_author_ids_result)],
            [(search_by_author_result)]
        ]

    result = search_by_author(author_name)
    if final_expected:
        assert result is not None
        assert "author_metadata" in result
    else:
        assert result is None


@pytest.mark.parametrize(
    "institution_name, get_institution_id_result, search_by_institution_result, found",
    [
        (
            "MyUniversity",
            [{"institution_id": 1415}],
            {
                "institution_metadata": {
                    "institution_name": "MyUniversity",
                    "openalex_url": "https://openalex.org/institution/5678",
                    "num_of_authors": 50,
                    "num_of_works": 100,
                },
                "data": [
                    {"topic_subfield": "CompSci", "num_of_authors": 25},
                    {"topic_subfield": "Biology", "num_of_authors": 20},
                ],
            },
            True
        ),
        (
            "NoSuchUniversity",
            None,
            None,
            False
        ),
    ],
    ids=["InstitutionFound", "InstitutionNotFound"]
)
@patch("backend.app.execute_query")
def test_search_by_institution_param(
    mock_exec, institution_name, get_institution_id_result, search_by_institution_result, found
):
    """
    Testing search_by_institution(...) with mocked DB results.
    """
    if get_institution_id_result is None:
        mock_exec.side_effect = [None]
    else:
        mock_exec.side_effect = [
            ([({'institution_id': get_institution_id_result[0]['institution_id']},)]),
            ([(search_by_institution_result,)])
        ]
    result = search_by_institution(institution_name)
    if found:
        assert result is not None
        assert "institution_metadata" in result
        assert result["institution_metadata"]["institution_name"] == institution_name
    else:
        assert result is None


@pytest.mark.parametrize(
    "topic_name, db_return, expect_result",
    [
        (
            "Chemistry",
            [{
                "subfield_metadata": [
                    {"topic": "Chemistry",
                     "subfield_url": "https://openalex.org/subfield/123"}
                ],
                "totals": {
                    "total_num_of_works": 999,
                    "total_num_of_citations": 3000,
                    "total_num_of_authors": 200
                },
                "data": [
                    {"institution_name": "Tech Labs University", "num_of_authors": 50},
                    {"institution_name": "State University", "num_of_authors": 100},
                ]
            }],
            True
        ),
        ("NonexistentTopic", None, False),
    ],
    ids=["TopicFound", "TopicNotFound"]
)
@patch("backend.app.execute_query")
def test_search_by_topic_param(mock_exec, topic_name, db_return, expect_result):
    """
    Testing search_by_topic(...) with different DB scenarios.
    """
    if db_return is None:
        mock_exec.return_value = None
    else:
        mock_exec.return_value = [db_return]

    result = search_by_topic(topic_name)
    if expect_result:
        assert result is not None
        assert "subfield_metadata" in result
        assert "totals" in result
    else:
        assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"author_metadata": {"dummy": "data"}}]])
def test_search_by_author_success(mock_exec, mock_get_author_ids):
    """
    If get_author_ids returns a valid author_id, check that search_by_author eventually returns data.
    """
    result = search_by_author("Test Author")
    assert result == {"author_metadata": {"dummy": "data"}}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_no_ids(mock_get_author_ids):
    result = search_by_author("Test Author")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result"}]])
def test_search_by_author_institution_topic_success(
    mock_exec,
    mock_get_institution_id,
    mock_get_author_ids
):
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result == {"dummy": "result"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_institution_topic_no_author_ids(mock_get_author_ids):
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_topic_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result2"}]])
def test_search_by_author_institution_success(
    mock_exec,
    mock_get_institution_id,
    mock_get_author_ids
):
    result = search_by_author_institution("Author", "Institution")
    assert result == {"dummy": "result2"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_institution_no_author_ids(mock_get_author_ids):
    result = search_by_author_institution("Author", "Institution")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    result = search_by_author_institution("Author", "Institution")
    assert result is None


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result3"}]])
def test_search_by_institution_topic_success(mock_exec, mock_get_institution_id):
    result = search_by_institution_topic("Institution", "Topic")
    assert result == {"dummy": "result3"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_topic_no_institution_id(mock_get_institution_id):
    result = search_by_institution_topic("Institution", "Topic")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"dummy": "result4"}]])
def test_search_by_author_topic_success(mock_exec, mock_get_author_ids):
    result = search_by_author_topic("Author", "Topic")
    assert result == {"dummy": "result4"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_topic_no_author_ids(mock_get_author_ids):
    result = search_by_author_topic("Author", "Topic")
    assert result is None


@patch("backend.app.execute_query", return_value=[[{"dummy": "result5"}]])
def test_search_by_topic_success(mock_exec):
    result = search_by_topic("Topic")
    assert result == {"dummy": "result5"}


@patch("backend.app.execute_query", return_value=None)
def test_search_by_topic_no_result(mock_exec):
    result = search_by_topic("Topic")
    assert result is None


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result6"}]])
def test_search_by_institution_success(mock_exec, mock_get_institution_id):
    result = search_by_institution("Institution")
    assert result == {"dummy": "result6"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_no_institution_id(mock_get_institution_id):
    result = search_by_institution("Institution")
    assert result is None
