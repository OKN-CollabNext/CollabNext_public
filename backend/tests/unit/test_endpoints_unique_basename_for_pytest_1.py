"""
Merged Tests: test_endpoints.py

This file consolidates all 'unit' tests from:
- test_endpoints.py
- test_search_edge_cases.py
- test_app_unit.py
- test_app_fallback.py
- test_sparql.py (unit)
- test_search_merged.py

Sections:
  1) LOGGER & FLASK ENDPOINT LOGGING TESTS
  2) EDGE CASES FOR /initial-search
  3) MOCKED REQUESTS TO OPENALEX (test_app_unit)
  4) FALLBACK LOGIC TESTS (test_app_fallback)
  5) SPARQL UNIT TESTS (pure mock)
  6) SEARCH-MERGED TESTS (mocked DB calls for search_by_* functions)
"""

import logging
import pytest
import requests
import responses
from unittest.mock import patch, MagicMock
from backend.app import (
    app,
    logger,
    setup_logger,
    fetch_last_known_institutions,
    SomeCustomError,
    initial_search,
    get_researcher_result,
    get_institution_results,
    get_researcher_and_subfield_results,
    search_by_author,
    search_by_author_institution_topic,
    search_by_author_institution,
    search_by_institution_topic,
    search_by_author_topic,
    search_by_topic,
    search_by_institution,
)


###############################################################################
# FIXTURES
###############################################################################

@pytest.fixture
def client():
    """
    Common Flask test client fixture for endpoint tests.
    """
    with app.test_client() as test_client:
        yield test_client


###############################################################################
# SECTION 1: LOGGER & FLASK ENDPOINT LOGGING TESTS (from original test_endpoints.py)
###############################################################################

@pytest.mark.parametrize(
    "log_message, log_level",
    [
        ("This is a test log message", logging.INFO),
        ("Another test message", logging.WARNING),
    ],
    ids=["InfoLog", "WarningLog"]
)
def test_logger_setup(caplog, log_message, log_level):
    """
    Tests that our custom logger logs messages at expected levels.
    """
    with caplog.at_level(log_level):
        logger.log(log_level, log_message)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == log_level
    assert log_message in caplog.text


@pytest.mark.parametrize(
    "flask_log_message, flask_log_level",
    [
        ("A Flask warning occurred", logging.WARNING),
        ("A Flask info occurred", logging.INFO),
    ],
    ids=["WarningCase", "InfoCase"]
)
def test_flask_app_logging(caplog, flask_log_message, flask_log_level):
    """
    Tests Flask’s builtin logger messages at different levels.
    """
    with caplog.at_level(flask_log_level):
        app.logger.log(flask_log_level, flask_log_message)
    assert flask_log_message in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == flask_log_level


def test_setup_logger_has_all_handlers(tmp_path):
    """
    Check that setup_logger() attaches at least 5 handlers:
      DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    from unittest.mock import patch
    logs_dir = tmp_path / "logs"
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.os.makedirs") as mock_makedirs:
        mock_exists.return_value = False
        test_logger = setup_logger()
        mock_makedirs.assert_called_once()

        assert len(test_logger.handlers) >= 5, "Expected at least five handlers."
        handler_levels = [handler.level for handler in test_logger.handlers]
        assert logging.DEBUG in handler_levels, "No DEBUG handler found."
        assert logging.INFO in handler_levels, "No INFO handler found."
        assert logging.WARNING in handler_levels, "No WARNING handler found."
        assert logging.ERROR in handler_levels, "No ERROR handler found."
        assert logging.CRITICAL in handler_levels, "No CRITICAL handler found."


###############################################################################
# SECTION 2: EDGE CASES FOR /initial-search (from test_search_edge_cases.py)
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
    assert response.status_code == 200, "Expected to handle None values gracefully."
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
        200, 400), "Expected safe fallback or 400 for invalid data."
    if response.is_json:
        data = response.get_json()
        assert isinstance(data, dict), "Expected a JSON dict even if invalid."


def test_initial_search_valid_author_only(client):
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


###############################################################################
# SECTION 3: MOCKED REQUESTS TO OPENALEX (from test_app_unit.py)
###############################################################################

def test_fetch_institutions_handles_http_error(requests_mock):
    """
    Confirm that a non-200 status code triggers SomeCustomError, using requests_mock.
    """
    requests_mock.get("https://api.openalex.org/authors/999", status_code=500)
    with pytest.raises(SomeCustomError):
        fetch_last_known_institutions("https://openalex.org/author/999")


@responses.activate
def test_fetch_institutions_responses_multiple():
    """
    Demonstrate using the responses library to handle multiple mocked HTTP calls.
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

    # This should raise SomeCustomError
    with pytest.raises(SomeCustomError):
        fetch_last_known_institutions("https://openalex.org/author/666")


###############################################################################
# SECTION 4: FALLBACK LOGIC TESTS (from test_app_fallback.py)
###############################################################################

def test_initial_search_exception(client):
    """
    If get_institution_researcher_subfield_results throws an exception,
    /initial-search should return an error JSON.
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


def test_get_researcher_result_fallback_success():
    """
    If DB (search_by_author) returns None, fallback calls get_author_metadata_sparql + list_given_researcher_institution.
    """
    dummy_metadata = {
        "oa_link": "dummy_oa",
        "name": "Test Author",
        "current_institution": "Test Institution"
    }
    dummy_list = [("topic1", 5)]
    dummy_graph = {
        "nodes": [
            {"id": "Test Institution", "label": "Test Institution", "type": "INSTITUTION"}
        ],
        "edges": []
    }
    with patch("backend.app.search_by_author", return_value=None), \
            patch("backend.app.get_author_metadata_sparql", return_value=dummy_metadata), \
            patch("backend.app.list_given_researcher_institution", return_value=(dummy_list, dummy_graph)):

        result = get_researcher_result("Test Author")
        assert isinstance(result, dict)
        assert result.get("metadata") == dummy_metadata
        assert result.get("graph") == dummy_graph
        assert result.get("list") == dummy_list


def test_get_researcher_result_fallback_no_results():
    """
    If DB returns None and SPARQL returns {}, we get an empty dict.
    """
    with patch("backend.app.search_by_author", return_value=None), \
            patch("backend.app.get_author_metadata_sparql", return_value={}):

        result = get_researcher_result("Test Author")
        assert result == {}


def test_get_institution_results_fallback_success():
    """
    If search_by_institution returns None, fallback to get_institution_metadata_sparql + list_given_institution.
    """
    dummy_metadata = {
        "ror": "dummy_ror",
        "name": "Dummy Inst",
        "works_count": "50",
        "cited_count": "100",
        "homepage": "dummy_homepage",
        "author_count": "20",
        "oa_link": "dummy_oa_link",
        "hbcu": False
    }
    dummy_list = [("subfield1", 10)]
    dummy_graph = {
        "nodes": [
            {"id": "dummy_inst", "label": "Dummy Inst", "type": "INSTITUTION"}
        ],
        "edges": []
    }

    with patch("backend.app.search_by_institution", return_value=None), \
            patch("backend.app.get_institution_metadata_sparql", return_value=dummy_metadata), \
            patch("backend.app.list_given_institution", return_value=(dummy_list, dummy_graph)):

        result = get_institution_results("Dummy Inst")
        assert isinstance(result, dict)
        assert result.get("metadata") == dummy_metadata
        assert result.get("graph") == dummy_graph
        assert result.get("list") == dummy_list


def test_get_institution_results_fallback_no_results():
    """
    If DB and SPARQL are empty, we get {}.
    """
    with patch("backend.app.search_by_institution", return_value=None), \
            patch("backend.app.get_institution_metadata_sparql", return_value={}):

        result = get_institution_results("Dummy Inst")
        assert result == {}


def test_get_researcher_and_subfield_results_fallback_success():
    """
    If search_by_author_topic returns None, fallback is get_topic_and_researcher_metadata_sparql + list_given_researcher_topic.
    """
    dummy_metadata = {
        "current_institution": "Test Institution",
        "topic_oa_link": "dummy_topic",
        "researcher_oa_link": "dummy_researcher",
        "institution_url": "dummy_inst",
        "work_count": 10,
        "cited_by_count": 50,
        "name": "Test Author",
        "orcid": "dummy_orcid"
    }
    dummy_work_list = [("Work1", 10)]
    dummy_graph = {"nodes": [
        {"id": "dummy_topic", "label": "Test Topic", "type": "TOPIC"}], "edges": []}
    dummy_extra_metadata = {"work_count": 10, "cited_by_count": 50}

    with patch("backend.app.search_by_author_topic", return_value=None), \
            patch("backend.app.get_topic_and_researcher_metadata_sparql", return_value=dummy_metadata), \
            patch("backend.app.list_given_researcher_topic", return_value=(dummy_work_list, dummy_graph, dummy_extra_metadata)):

        result = get_researcher_and_subfield_results(
            "Test Author", "Test Topic")
        assert isinstance(result, dict)
        assert result.get("metadata") == dummy_metadata
        assert result.get("graph") == dummy_graph
        assert result.get("list") == dummy_work_list


def test_get_researcher_and_subfield_results_fallback_no_results():
    """
    If DB returns None and SPARQL returns {}, final result is {}.
    """
    with patch("backend.app.search_by_author_topic", return_value=None), \
            patch("backend.app.get_topic_and_researcher_metadata_sparql", return_value={}):

        result = get_researcher_and_subfield_results(
            "Test Author", "Test Topic")
        assert result == {}


###############################################################################
# SECTION 5: SPARQL UNIT TESTS (pure mock) from test_sparql.py (unit version)
###############################################################################

@patch("backend.app.requests.post")
def test_query_SPARQL_endpoint_success_unit(mock_post):
    """
    Unit test: Mocks a successful SPARQL endpoint POST request.
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

    result = app.query_SPARQL_endpoint("http://example.com", "SELECT *")
    assert isinstance(result, list)
    assert result == [{"var1": "val1", "var2": "val2"}]


@patch("backend.app.requests.post", side_effect=requests.exceptions.RequestException("Error"))
def test_query_SPARQL_endpoint_failure_unit(mock_post):
    """
    Unit test: If the POST fails, we expect an empty list from the function.
    """
    result = app.query_SPARQL_endpoint("http://example.com", "SELECT *")
    assert result == []


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_institution_metadata_sparql_no_results_unit(mock_query):
    """
    Unit test: get_institution_metadata_sparql(...) returns {} if no SPARQL results.
    """
    result = app.get_institution_metadata_sparql("Nonexistent")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_institution_metadata_sparql_valid_unit(mock_query):
    """
    Unit test: Checks parsing institution fields from a valid SPARQL response.
    """
    mock_query.return_value = [{
        "ror": "ror123",
        "workscount": "100",
        "citedcount": "200",
        "homepage": "http://homepage",
        "institution": "semopenalex/institution/abc",
        "peoplecount": "50"
    }]
    result = app.get_institution_metadata_sparql("Test Institution")
    assert result["ror"] == "ror123"
    assert result["works_count"] == "100"
    assert result["homepage"] == "http://homepage"
    assert "openalex" in result["oa_link"]


@patch("backend.app.query_SPARQL_endpoint", return_value=[])
def test_get_author_metadata_sparql_no_results_unit(mock_query):
    """
    Unit test: get_author_metadata_sparql(...) returns {} if no SPARQL results.
    """
    result = app.get_author_metadata_sparql("Nonexistent Author")
    assert result == {}


@patch("backend.app.query_SPARQL_endpoint")
def test_get_author_metadata_sparql_valid_unit(mock_query):
    """
    Unit test: Checks parsing author fields from a valid SPARQL response.
    """
    mock_query.return_value = [{
        "cite_count": "300",
        "orcid": "orcid123",
        "works_count": "50",
        "current_institution_name": "Test Univ",
        "author": "semopenalex/author/xyz",
        "current_institution": "semopenalex/institution/inst"
    }]
    result = app.get_author_metadata_sparql("Test Author")
    assert result["cited_by_count"] == "300"
    assert result["orcid"] == "orcid123"
    assert "openalex" in result["oa_link"]


###############################################################################
# SECTION 6: SEARCH-MERGED TESTS (from test_search_merged.py)
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
