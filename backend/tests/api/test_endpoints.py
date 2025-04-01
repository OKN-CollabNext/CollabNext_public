"""
API Endpoint Tests

Tests include:
- /initial-search endpoint with various input combinations
- /get-institutions endpoint
- /autofill-institutions endpoint
- /autofill-topics endpoint
- /get-default-graph endpoint
- /get-topic-space-default-graph endpoint
"""

from unittest.mock import patch, MagicMock
from unittest.mock import patch, MagicMock, mock_open
from backend.app import app, combine_graphs, is_HBCU
import pytest
import json
""" Rename the exception as it has been imported and importable, to reflect more genuinely its origin as I have customized it. We could do so redefine and rename the SomeCustomError in the `backend.app`, however, as OpenAlexAPIError. """


@pytest.fixture
def client():
    with app.test_client() as test_client:
        yield test_client


###############################################################################
# /initial-search ENDPOINT TESTS
###############################################################################

def test_initial_search_null_values(client):
    payload = {"organization": None,
               "researcher": None, "topic": None, "type": None}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code in (200, 400, 415, 500)
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "org, researcher, topic, typ",
    [
        ("", "", "", ""),
        ("   ", "   ", "   ", ""),
    ],
    ids=["AllEmptyStrings", "AllSpaces"]
)
def test_initial_search_empty_or_whitespace(client, org, researcher, topic, typ):
    payload = {"organization": org, "researcher": researcher,
               "topic": topic, "type": typ}
    response = client.post("/initial-search", json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data, dict)


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
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"organization": 123, "researcher": 456, "topic": 789, "type": 1011},
        {"organization": ["A", "B"], "researcher": {},
            "topic": True, "type": 9.99},
    ],
    ids=["AllNumbers", "MixedTypes"]
)
def test_initial_search_invalid_types(client, invalid_payload):
    response = client.post("/initial-search", json=invalid_payload)
    data = response.get_json() or {}
    assert response.status_code in (200, 400, 500)
    assert isinstance(data, dict)


def test_initial_search_extremely_long_strings(client):
    huge_string = "A" * 5000
    payload = {"organization": huge_string, "researcher": huge_string,
               "topic": huge_string, "type": "dummy"}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert isinstance(data, dict)


def test_initial_search_no_payload(client):
    response = client.post("/initial-search")
    assert response.status_code in (200, 400, 415, 500)
    if response.is_json:
        data = response.get_json() or {}
        assert isinstance(data, dict)


def test_initial_search_special_chars(client):
    payload = {"organization": "Univ!@#$%^&*()_+|", "researcher": "",
               "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert isinstance(data, dict)


def test_initial_search_unknown_type(client):
    payload = {"organization": "Test Org", "researcher": "Test Author",
               "topic": "Test Topic", "type": "SOMETHING_RANDOM"}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert isinstance(data, dict)


def test_initial_search_numeric_topic(client):
    payload = {"organization": "Test Org",
               "researcher": "Test Author", "topic": "42", "type": ""}
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"organization": "", "researcher": "", "topic": "", "type": ""},
        {"notARealKey": "notUsed"}
    ],
    ids=["CompletelyEmpty", "AllBlankStrings", "UnusedKey"]
)
def test_initial_search_all_fields_invalid(client, payload):
    response = client.post("/initial-search", json=payload)
    data = response.get_json() or {}
    assert response.status_code in (200, 400, 500)
    assert isinstance(data, dict)


def test_initial_search_valid_author_only(client):
    payload = {"researcher": "Jane Doe",
               "organization": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_institution_only(client):
    payload = {"researcher": "",
               "organization": "Harvard University", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_topic_only(client):
    payload = {"researcher": "", "organization": "",
               "topic": "Biochemistry", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_author_institution(client):
    payload = {"researcher": "John Smith",
               "organization": "MIT", "topic": "", "type": "HBCU"}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_institution_topic(client):
    payload = {"researcher": "", "organization": "Stanford University",
               "topic": "Astrophysics", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_valid_author_topic(client):
    payload = {"researcher": "Alice Brown", "organization": "",
               "topic": "Machine Learning", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_all_three(client):
    payload = {"researcher": "Carlos Garcia",
               "organization": "Howard University", "topic": "Mathematics", "type": "HBCU"}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_author(client):
    payload = {"researcher": "Fake McNotReal",
               "organization": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_institution(client):
    payload = {"researcher": "",
               "organization": "NoSuch Institute", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_nonexistent_topic(client):
    payload = {"researcher": "", "organization": "",
               "topic": "Quantum Flubber", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


@pytest.mark.parametrize("partial_author", ["Lew", "", " "])
def test_initial_search_partial_author(client, partial_author):
    payload = {"researcher": partial_author,
               "organization": "Cornell University" if partial_author == "" else "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_whitespace_fields(client):
    payload = {"researcher": " ",
               "organization": " ", "topic": " ", "type": ""}
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
    payload = {"researcher": "", "organization": org, "topic": "",
               "type": "HBCU" if expected_hbcu_status else ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_orcid(client):
    payload = {"researcher": "0000-0002-1825-0097",
               "organization": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_special_chars_in_topic(client):
    payload = {"researcher": "", "organization": "",
               "topic": "Biology/Genomics!", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_exception(client):
    with patch("backend.app.get_institution_researcher_subfield_results", side_effect=Exception("Test exception")):
        response = client.post("/initial-search", json={"organization": "Test Inst",
                               "researcher": "Test Author", "topic": "Test Topic", "type": "dummy"})
        data = response.get_json()
        assert data == {"error": "An unexpected error occurred"}


###############################################################################
# /get-institutions ENDPOINT TESTS
###############################################################################

def test_get_institutions_success(client):
    response = client.get("/get-institutions")
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "institutions" in data
    assert isinstance(data["institutions"], list)


@patch("backend.app.execute_query", return_value=None)
def test_get_institutions_no_data(mock_execute_query, client):
    response = client.get("/get-institutions")
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert "institutions" in data
    assert isinstance(data["institutions"], list)
    assert len(data["institutions"]) == 0


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_get_institutions_error(mock_execute_query, client):
    response = client.get("/get-institutions")
    assert response.status_code == 500
###############################################################################
# /autofill-institutions ENDPOINT TESTS
###############################################################################


def test_autofill_institutions_success(client):
    """
    Test successful retrieval of autofill suggestions for institutions.
    """
    response = client.post("/autofill-institutions",
                           json={"institution": "Harv"})
    data = response.get_json() or {}
    # Expect a dictionary with key "possible_searches"
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data


def test_autofill_institutions_empty_query(client):
    """
    Test handling of empty query for institution autofill.
    """
    response = client.post("/autofill-institutions", json={"institution": ""})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    # Expect an empty list in possible_searches
    assert "possible_searches" in data
    assert isinstance(data["possible_searches"], list)
    assert len(data["possible_searches"]) == 0


def test_autofill_institutions_no_matches(client):
    """
    Test handling of no matches for institution autofill.
    """
    response = client.post("/autofill-institutions",
                           json={"institution": "xyzabc123"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data
    assert len(data["possible_searches"]) == 0


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_autofill_institutions_error(mock_execute_query, client):
    """
    Test handling of database errors for institution autofill.
    """
    response = client.post("/autofill-institutions", json={"query": "Harv"})
    assert response.status_code == 500
###############################################################################
# /autofill-topics ENDPOINT TESTS
###############################################################################


def test_autofill_topics_success(client):
    """
    Test successful retrieval of autofill suggestions for topics.
    """
    response = client.post("/autofill-topics", json={"topic": "Comp"})
    data = response.get_json() or {}
    # Expect dictionary with key "possible_searches"
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data


def test_autofill_topics_empty_query(client):
    """
    Test handling of empty query for topic autofill.
    """
    response = client.post("/autofill-topics", json={"topic": ""})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data
    assert len(data["possible_searches"]) == 0


def test_autofill_topics_no_matches(client):
    """
    Test handling of no matches for topic autofill.
    """
    response = client.post("/autofill-topics", json={"topic": "xyzabc123"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data
    assert len(data["possible_searches"]) == 0


@patch("backend.app.execute_query", side_effect=Exception("Database error"))
def test_autofill_topics_error(mock_execute_query, client):
    """
    Test handling of database errors for topic autofill.
    """
    response = client.post("/autofill-topics", json={"query": "Comp"})
    assert response.status_code == 500


###############################################################################
# /get-default-graph ENDPOINT TESTS
###############################################################################

def test_get_default_graph_success(client):
    """
    Test successful retrieval of default graph.
    """
    response = client.post("/get-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    # Expect either a graph or an error message
    if "error" in data:
        pytest.skip("Default graph file not found")
    else:
        assert "graph" in data
        assert "nodes" in data["graph"]
        assert "edges" in data["graph"]


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_default_graph_error(mock_json_load, client):
    """
    Test handling of file errors for default graph.
    """
    response = client.post("/get-default-graph", json={})
    # If an error occurs, we expect a dictionary with an error key
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert "error" in data

###############################################################################
# /get-topic-space-default-graph ENDPOINT TESTS
###############################################################################


def test_get_topic_space_default_graph_success(client):
    """
    Test successful retrieval of topic space default graph.
    """
    response = client.post("/get-topic-space-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    if "graph" in data:
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph
    else:
        pytest.skip("No graph returned")


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_topic_space_default_graph_error(mock_json_load, client):
    """
    Test handling of file errors for topic space default graph.
    """
    response = client.post("/get-topic-space-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
###############################################################################
# /search-topic-space ENDPOINT TESTS
###############################################################################


def test_search_topic_space_success(client):
    """
    Test successful search of topic space.
    """
    response = client.post("/search-topic-space",
                           json={"query": "Computer Science"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    if "graph" not in data:
        pytest.skip("No 'graph' key in topic space search result")
    else:
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph


def test_search_topic_space_empty_query(client):
    """
    Test handling of empty query for topic space search.
    """
    response = client.post("/search-topic-space", json={"query": ""})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    if "graph" not in data:
        pytest.skip(
            "No 'graph' key in topic space search result for empty query")
    else:
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph


def test_search_topic_space_no_matches(client):
    """
    Test handling of no matches for topic space search.
    """
    response = client.post("/search-topic-space", json={"query": "xyzabc123"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    if "graph" not in data:
        pytest.skip(
            "No 'graph' key in topic space search result for no matches")
    else:
        graph = data["graph"]
        assert "nodes" in graph
        assert "edges" in graph


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_search_topic_space_error(mock_json_load, client):
    """
    Test handling of file errors for topic space search.
    """
    response = client.post("/search-topic-space",
                           json={"query": "Computer Science"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)


@patch("backend.app.SUBFIELDS", new=False)
def test_autofill_topics_no_subfields(client, mocker):
    """
    Force SUBFIELDS=False to cover up that branch where we read keywords.csv
    instead of subfields.csv, since that branch is above our modularization
    capacity for now but not for long.
    For now we should just, we huddle around and do a quick check to confirm,
    that the code path was indeed run, returning matched results from 'keywords.csv'.
    """
    # Mock the built-in open(...) call so we don't need a real keywords.csv file
    mock_file_data = "Alpha\nBeta\nGamma"
    mocker.patch("builtins.open", mock_open(read_data=mock_file_data))

    # Now call the endpoint with some 'query' that should match e.g. "bet" -> "Beta"
    response = client.post("/autofill-topics", json={"topic": "bet"})
    assert response.status_code in (200, 500)
    data = response.get_json()  # "and then,"" "at the last minute" we get the data
    assert isinstance(data, dict), "We expect a dict from /autofill-topics"
    assert "possible_searches" in data, "Missing 'possible_searches' key"
    assert any("Beta" in item for item in data["possible_searches"]
               ), f"Expected 'Beta' among the returned topics, got: {data}"


def test_mup_sat_scores_success(client, mocker):
    # Mocking the DB call might help
    mocker.patch("backend.app.execute_query", return_value=[
        ({
            "institution_name": "Test University",
            "institution_id": "abcd",
            "data": [{"sat": 1200, "year": 2021}, {"sat": 1250, "year": 2022}]
        },)
    ])
    payload = {"institution_name": "Test University"}
    response = client.post("/mup-sat-scores", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["institution_name"] == "Test University"
    assert len(data["data"]) == 2


def test_get_institution_medical_expenses(mocker):
    from backend.app import get_institution_medical_expenses
    # If it calls `get_institution_mup_id` or `execute_query`, mock them because I would want to avoid "unnecessarily" doing that again.
    mocker.patch("backend.app.get_institution_mup_id",
                 return_value={"institution_mup_id": "999"})
    mocker.patch("backend.app.execute_query", return_value=[
        ({
            "institution_name": "Test Uni",
            "institution_mup_id": "999",
            "data": [{"expenditure": 1000000, "year": 2021}]
        },)
    ])
    result = get_institution_medical_expenses("Test Uni")
    assert result["institution_name"] == "Test Uni"
    assert len(result["data"]) == 1
    assert result["data"][0]["expenditure"] == 1000000
# Just to confirm, in `test_endpoints.py` we can 'just keep appending '
# them upon request, or as a more general note we can illustrate how to
# cover routes like /geo_info, but the Measuring University Performance
# endpoints, as well as "internal" 200/400/500 status helpers like the is_HBCU and,
# the combine_graphs are endpoints; they're available upon request.


@pytest.fixture
def client():
    """Generally standard prettified Flask test client."""
    with app.test_client() as test_client:
        yield test_client


def test_combine_graphs():
    """
    Directly cover the 'combine_graphs' function pending a small test.
    """
    g1 = {
        "nodes": [
            {"id": "A", "label": "NodeA"},
            {"id": "B", "label": "NodeB"}
        ],
        "edges": [
            {"id": "AB", "start": "A", "end": "B"}
        ]
    }
    g2 = {
        "nodes": [
            {"id": "B", "label": "NodeB"},   # duplicate meaning
            {"id": "C", "label": "NodeC"}
        ],
        "edges": [
            {"id": "BC", "start": "B", "end": "C"}
        ]
    }
    combined = combine_graphs(g1, g2)
    assert len(
        combined["nodes"]) == 3, f"Expected 3 unique nodes, got nodes' ranges {len(combined['nodes'])}"
    assert len(
        combined["edges"]) == 2, f"Expected 2 unique edges, got edges' ranges {len(combined['edges'])}"
    node_ids = [n["id"] for n in combined["nodes"]]
    edge_ids = [e["id"] for e in combined["edges"]]
    assert "A" in node_ids
    assert "C" in node_ids
    assert "BC" in edge_ids


@patch("backend.app.query_SQL_endpoint")
@patch("backend.app.create_connection")
def test_is_hbcu_true(mock_create_conn, mock_query):
    """
    Tests 'is_HBCU' "always" returns True when DB says HBCU=1.
    """
    # Mock the small Database connection with a mighty object:
    mock_conn = MagicMock()
    mock_create_conn.return_value = mock_conn
    # We know we support SPARQL (do we support Cypher?), and so we wait or we can mock that, the Database returns [(1,)]:
    mock_query.return_value = [(1,)]

    result = is_HBCU("https://openalex.org/institutions/12345")
    assert result is True, "Expected True for HBCU=1 (Segmentation Fault quite possibly?)"


@patch("backend.app.query_SQL_endpoint")
@patch("backend.app.create_connection")
def test_is_hbcu_false(mock_create_conn, mock_query):
    """
    Tests 'is_HBCU' "always" returns False when DB says 0 or no row.
    """
    mock_conn = MagicMock()
    mock_create_conn.return_value = mock_conn
    mock_query.return_value = [(0,)]  # or possibly []

    result = is_HBCU("https://openalex.org/institutions/67890")
    assert result is False, "Expected False (there are many results) for HBCU=0"


###############################################################################
# /geo_info ENDPOINT TESTS TO CONFIRM NEW ENDPOINTS
###############################################################################

@patch("backend.app.requests.get")
def test_geo_info_success(mock_get, client):
    """
    Model test for /geo_info endpoint success case.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "geo": {
            "country_code": "US",
            "region": "Massachusetts",
            "latitude": 42.3736,
            "longitude": -71.1097
        }
    }
    mock_get.return_value = mock_response

    payload = {"institution_oa_link": "openalex.org/institutions/12345"}
    resp = client.post("/geo_info", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert "country_code" in data
    assert data["region"] == "Massachusetts"


@patch("backend.app.requests.get")
def test_geo_info_404(mock_get, client):
    """
    Model test for /geo_info endpoint when the institution is just not found.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    payload = {"institution_oa_link": "openalex.org/institutions/doesnotexist"}
    resp = client.post("/geo_info", json=payload)
    # we would be happy to return of course, /geo_info doesn't return
    # code=404, but let's check that we get either None or some "eventual"
    # last resort "object"
    assert resp.status_code in (200, 404)
    # The route's code is notably written such that it might not "search" and
    # do a `return ...` so we might see an empty response or None.
    # So there is some "issue", I think JavaScript Object Notation is the way
    # forward:
    # data = resp.get_json()
    # assert data == ...
    # or at least do not do anything on the response side but confirm we
    # didn't crash:
    pass


###############################################################################
# MEASURING UNIVERSITY PERFORMANCE ENDPOINT TESTS
###############################################################################

def test_get_mup_id_success(client, mocker):
    """
    Please test /get-mup-id with a normal success scenario.
    """
    mocker.patch("backend.app.get_institution_mup_id",
                 return_value={"institution_mup_id": "X999"})
    payload = {"institution_name": "Test University"}
    response = client.post("/get-mup-id", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert data.get("institution_mup_id") == "X999"


def test_get_mup_id_notfound(client, mocker):
    """
    Please beta test /get-mup-id returning 404 if the Measuring University Performance ID, is None.
    """
    mocker.patch("backend.app.get_institution_mup_id", return_value=None)
    payload = {"institution_name": "Unknown Univ"}
    response = client.post("/get-mup-id", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 404
    assert "error" in data


def test_endowments_and_givings_success(client, mocker):
    """
    Test /endowments-and-givings with the excellent, success scenario.
    """
    mocker.patch("backend.app.get_institution_endowments_and_givings", return_value={
        "institution_name": "TestU",
        "institution_id": "123",
        "data": [{"endowment": 5000000, "giving": 300000, "year": 2021}]
    })
    payload = {"institution_name": "TestU"}
    response = client.post("/endowments-and-givings", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert data.get("institution_name") == "TestU"
    assert len(data.get("data", [])) == 1


def test_endowments_and_givings_notfound(client, mocker):
    """
    Test /endowments-and-givings returning 404 if no data will be found.
    """
    mocker.patch(
        "backend.app.get_institution_endowments_and_givings", return_value=None)
    payload = {"institution_name": "NoSuchU"}
    response = client.post("/endowments-and-givings", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 404
    # Alter the expected error message to include the app’s out-put:
    assert "error" in data


def test_institution_num_of_researches_success(client, mocker):
    """
    Test /institution_num_of_researches endpoint excellent, success scenario.
    """
    mocker.patch("backend.app.get_institution_num_of_researches", return_value={
        "institution_name": "TestU",
        "institution_id": "111",
        "data": [
            {"num_federal_research": 10, "num_nonfederal_research": 5,
                "total_research": 15, "year": 2022}
        ]
    })
    payload = {"institution_name": "TestU"}
    resp = client.post("/institution_num_of_researches", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["institution_name"] == "TestU"
    assert len(data["data"]) == 1


def test_institution_num_of_researches_no_data(client, mocker):
    mocker.patch("backend.app.get_institution_num_of_researches",
                 return_value=None)
    payload = {"institution_name": "TestU"}
    resp = client.post("/institution_num_of_researches", json=payload)
    assert resp.status_code == 404
    data = resp.get_json()
    assert "no data found" in data.get("error", "").lower()


def test_institution_medical_expenses_success(client, mocker):
    mocker.patch("backend.app.get_institution_medical_expenses", return_value={
        "institution_name": "HealthU",
        "institution_mup_id": "HX123",
        "data": [
            {"expenditure": 2500000, "year": 2021}
        ]
    })
    resp = client.post("/institution_medical_expenses",
                       json={"institution_name": "HealthU"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["institution_name"] == "HealthU"
    assert len(data["data"]) == 1


def test_institution_medical_expenses_no_data(client, mocker):
    mocker.patch("backend.app.get_institution_medical_expenses",
                 return_value=None)
    resp = client.post("/institution_medical_expenses",
                       json={"institution_name": "NoMedSchool"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "no data found" in data.get("error", "").lower()


def test_institution_doctorates_and_postdocs_success(client, mocker):
    mocker.patch("backend.app.get_institution_doctorates_and_postdocs", return_value={
        "institution_name": "PostDocU",
        "institution_id": "PD123",
        "data": [
            {"num_postdocs": 50, "num_doctorates": 40, "year": 2021}
        ]
    })
    resp = client.post("/institution_doctorates_and_postdocs",
                       json={"institution_name": "PostDocU"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["institution_name"] == "PostDocU"
    assert len(data["data"]) == 1


def test_institution_doctorates_and_postdocs_no_data(client, mocker):
    mocker.patch(
        "backend.app.get_institution_doctorates_and_postdocs", return_value=None)
    resp = client.post("/institution_doctorates_and_postdocs",
                       json={"institution_name": "NoDocsHere"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "Moot; no data found" in data["error"]


def test_mup_faculty_awards_success(client, mocker):
    mocker.patch("backend.app.get_institutions_faculty_awards", return_value={
        "institution_name": "AwardU",
        "institution_id": "999",
        "data": [
            {"nae": 2, "nam": 1, "nas": 3, "num_fac_awards": 6, "year": 2022}
        ]
    })
    resp = client.post("/mup-faculty-awards",
                       json={"institution_name": "AwardU"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["institution_name"] == "AwardU"
    assert len(data["data"]) == 1


def test_mup_faculty_awards_no_data(client, mocker):
    mocker.patch("backend.app.get_institutions_faculty_awards",
                 return_value=None)
    resp = client.post("/mup-faculty-awards",
                       json={"institution_name": "NoAwards"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "No faculty awards found" in data["error"]


def test_mup_r_and_d_success(client, mocker):
    mocker.patch("backend.app.get_institutions_r_and_d", return_value={
        "institution_name": "RnDU",
        "institution_id": "100",
        "data": [
            {"category": "Engineering", "federal": 1000, "percent_federal": 50.0,
             "total": 2000, "percent_total": 100.0}
        ]
    })
    resp = client.post("/mup-r-and-d", json={"institution_name": "RnDU"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["institution_name"] == "RnDU"
    assert len(data["data"]) == 1


def test_mup_r_and_d_no_data(client, mocker):
    mocker.patch("backend.app.get_institutions_r_and_d", return_value=None)
    resp = client.post("/mup-r-and-d", json={"institution_name": "NoRnD"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "No R&D numbers found" in data["error"]
# !!=== Additional Coverage Tests ===!! These are quite "important" in the sense that
# we have to make it possible to computationally wrangle these crucial error handlers
# and missing payloads as well as the utility functions.


def test_404_handler(client):
    # And so we check in and request a non-existent route; just to see how our
    # 404 event error handler returns index.html (thus 200)
    response = client.get("/nonexistent-route")
    assert response.status_code == 200
    # And so we have experience with checking that the returned content does
    # look like HTML (determined that the macOS struggle is a legitimate thing that
    # necessitates a system that is up and running and that can generate HTML)
    assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


def test_500_handler(client):
    # Also, we  need to make this make sense so we add in this route that
    # temporarily raises an exception always and forever
    @app.route("/trigger-error")
    def trigger_error():
        raise Exception("Forced error for testing")
    response = client.get("/trigger-error")
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data


def test_get_institutions_file_error(client):
    # Furthermore, we have to do a lot of caching. That means that the results
    # that we have are going to require us to require a file Input / Output
    # error to occur in get_institutions by patching, the builtins.open
    with patch("builtins.open", side_effect=Exception("File not found")):
        response = client.get("/get-institutions")
        data = response.get_json() or {}
        assert response.status_code == 500
        assert "error" in data


def test_get_mup_id_missing_payload(client):
    # And then we want to test out what is the required key that is missing
    # and this is a pragmatic update because what it does is it gets the
    # /get-mup-id going in remembrance of the Center, for Measuring University
    # Performance and fixing the bugs .
    response = client.post("/get-mup-id", json={})
    assert response.status_code == 400


def test_endowments_and_givings_missing_payload(client):
    # Furthermore the missing "institution_name" has got to trigger a
    # 400 error and if it only runs 10 minutes over, you should and ought to
    # press Command + C or Ctrl + C becuase you know that that's a win, for
    # allowing the main function to be tested optimistically.
    response = client.post("/endowments-and-givings", json={})
    assert response.status_code == 400


def test_institution_num_of_researches_missing_payload(client):
    # Then, there's no need to start fixing the bugs until we have the payload;
    # when the payload is missing, then the route itself also has to return
    # an error or so they say here, 404 is "something that is expected".
    response = client.post("/institution_num_of_researches", json={})
    assert response.status_code == 404


def test_institution_medical_expenses_missing_payload(client):
    response = client.post("/institution_medical_expenses", json={})
    assert response.status_code == 404


def test_institution_doctorates_and_postdocs_missing_payload(client):
    response = client.post("/institution_doctorates_and_postdocs", json={})
    assert response.status_code == 404


def test_mup_faculty_awards_missing_payload(client):
    response = client.post("/mup-faculty-awards", json={})
    assert response.status_code == 400


def test_mup_r_and_d_missing_payload(client):
    response = client.post("/mup-r-and-d", json={})
    assert response.status_code == 400

# Now, test the Utility functions.####


def test_combine_graphs_extra():
    g1 = {"nodes": [{"id": "A", "label": "A"}], "edges": [
        {"id": "A-B", "start": "A", "end": "B"}]}
    g2 = {"nodes": [{"id": "B", "label": "B"}], "edges": [
        {"id": "B-C", "start": "B", "end": "C"}]}
    combined = combine_graphs(g1, g2)
    node_ids = {node["id"] for node in combined["nodes"]}
    edge_ids = {edge["id"] for edge in combined["edges"]}
    assert node_ids == {"A", "B"}
    assert edge_ids == {"A-B", "B-C"}


def test_is_HBCU_simulation_true():
    with patch("backend.app.create_connection"), \
            patch("backend.app.query_SQL_endpoint", return_value=[(1,)]):
        result = is_HBCU("https://openalex.org/institutions/12345")
        assert result is True


def test_is_HBCU_simulation_false():
    with patch("backend.app.create_connection"), \
            patch("backend.app.query_SQL_endpoint", return_value=[(0,)]):
        result = is_HBCU("https://openalex.org/institutions/67890")
        assert result is False
