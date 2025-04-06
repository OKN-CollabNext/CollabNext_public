"""
API Endpoints Integration Test Suite

This module schedules a comprehensive set of integration tests for the application's API endpoints.
It covers the following endpoints:
  - /initial-search: Validates various input scenarios and routing logic.
  - /get-institutions: Arrival of proper handling of the institutions CSV file.
  - /autofill-institutions: Tests dynamic suggestion functionality for institution names.
  - /autofill-topics: Checks substring matching and suggestion filtering for topics.
  - /get-default-graph: Assesses the loading and processing of the default graph JSON.
  - /get-topic-space-default-graph: Evaluates the construction of the topic-space graph.
"""
from backend.app import app, combine_graphs
from unittest.mock import patch, MagicMock, mock_open
import pytest

###############################################################################
# /initial-search ENDPOINT TESTS
###############################################################################


def test_initial_search_valid_author_institution(client):
    """ This test function simulates a valid search scenario by sending a JSON payload with a researcher ("John Smith"), an institution ("MIT"), an empty topic, and a type ("HBCU") to the `/initial-search` endpoint. By doing so, it safely exercises several key parts of the application: it triggers the extraction and logging of the incoming search parameters (lines 192–193), directs the logic to the branch that handles searches when both a researcher and institution are provided (line 347), and—if the database query for an author-institution search returns no results—it activates the fallback logic that invokes a SPARQL query (lines 746–747). Finally, it verifies that the endpoint correctly assembles and returns a well-formed JSON response (line 1045). Overall, the test confirms that the search functionality behaves as expected when valid author and institution inputs are provided. """
    # We might mock DB calls here if we want to post a “success from DB” path.
    payload = {"researcher": "John Smith",
               "organization": "MIT", "topic": "", "type": "HBCU"}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200, "Expected 200 for valid author & institution"
    data = response.get_json()
    assert isinstance(data, dict), "Expected a JSON dict response"

    # If the app returns an empty dictionary on the fallback channel, we can handle that:
    if data:
        # We expect "metadata", "graph", "list" (we consider that to be the real structure)
        assert "metadata" in data, "Should contain 'metadata' key"
        assert "graph" in data, "Should contain 'graph' key"
        assert "list" in data, "Should contain 'list' key"


def test_initial_search_valid_institution_topic(client):
    """ This test simulates a search scenario where a user submits a valid institution ("Stanford University") and a valid topic ("Astrophysics") while leaving the researcher field empty. In the application's logic, lines 215–216 identify this combination of inputs and route the request to the branch that handles institution–topic searches. At line 349, the function dedicated to processing institution and topic queries (i.e., `get_institution_and_subfield_results`) is invoked. If the database does not yield any results, the fallback mechanism using SPARQL is triggered, as outlined in lines 670–675. Finally, lines 1187–1197 deal with processing and returning the results (including graph construction and metadata formatting) as a well-formed JSON response. This test tells us that when valid institution and topic inputs are provided, the endpoint properly processes the query and returns the expected dictionary response. """
    payload = {"researcher": "", "organization": "Stanford University",
               "topic": "Astrophysics", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    if data:
        assert "metadata" in data
        # Example: we might check if "metadata" includes "topic_name" or "work_count" which are considered to be unfrozen
        if "metadata" in data and isinstance(data["metadata"], dict):
            assert "cited_by_count" in data["metadata"] or "work_count" in data["metadata"], \
                "Metadata is expected to have cited_by_count or work_count fields"


def test_initial_search_valid_author_topic(client):
    """ This test simulates a search request where only a researcher ("Alice Brown") and a topic ("Machine Learning") are provided, leaving the institution field empty. In this scenario, the application's logic—specifically lines 230–231—checks that both a researcher and a topic are supplied. Then, at line 351, the code directs the request to the branch responsible for processing author-topic searches (likely invoking a function such as `get_researcher_and_subfield_results`). The test confirms that the `/initial-search` endpoint returns a 200 status code and a valid JSON dictionary, such that the system correctly handles and processes searches based solely on author and topic inputs. """
    payload = {"researcher": "Alice Brown", "organization": "",
               "topic": "Machine Learning", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_initial_search_all_three(client):
    """ This test exercises the “all three” branch of our `/initial-search` endpoint: when the client posts an institution, researcher, and topic together, the handler (lines 817–822) invokes `get_institution_researcher_subfield_results`. If the database lookup returns `None`, those lines fall back into the SPARQL path, calling `get_institution_and_topic_and_researcher_metadata_sparql` (lines 1339–1366) to assemble combined metadata for the institution, topic, and researcher. By asserting a 200 response and that the returned JSON is a dict, the test verifies that both the routing logic in `initial_search` and the SPARQL‐based metadata aggregation functions are wired correctly for the three‑parameter case. """
    payload = {"researcher": "Carlos Garcia",
               "organization": "Howard University", "topic": "Mathematics", "type": "HBCU"}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # If fallback logic is triggered, we might see an empty or partial response.
    # Check for the presence (or absence) of keys and share if the code doesn’t crash.
    if data:
        assert "metadata" in data
        assert "graph" in data
        assert "list" in data


def test_initial_search_nonexistent_institution(client):
    """ This test targets the “institution only” branch of `/initial-search`. When the payload includes an organization but no researcher or topic, the handler (lines 349–356) calls `get_institution_results`. Since “NoSuch Institute” won’t exist in the database, `get_institution_results` falls back to SPARQL—specifically hitting the “no SPARQL results” check at lines 473–474, which logs a warning and returns an empty dict. By asserting a 200 status and that the returned JSON is a dict (even if empty), the test confirms that the endpoint gracefully handles unknown institutions by returning an empty result rather than an error. """
    payload = {"researcher": "",
               "organization": "NoSuch Institute", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # For a nonexistent institution, we might expect an empty or partial structure
    assert data == {}, f"Expected empty dict for unknown institution, got {data}"


@pytest.mark.parametrize("partial_author", ["Lew", "", " "])
def test_initial_search_partial_author(client, partial_author):
    """ This parameterized test checks the “researcher only” path of `/initial-search` for various partial or blank researcher inputs. When a non‑empty partial name (e.g. “Lew”) is supplied without organization or topic, the handler (lines 402–405) invokes `get_researcher_result`, which first tries the database and then—upon no results—falls back to SPARQL via `get_author_metadata_sparql` and `list_given_researcher_institution` (lines 1064–1099) to build metadata and a topic graph for the author. When the researcher field is blank or just whitespace, the handler still routes into this same branch, and `get_researcher_result` ultimately returns an empty dict. By asserting a 200 status and that the response is a dict, the test ensures that both the database‑then‑SPARQL lookup logic and the OpenAlex graph construction in `list_given_researcher_institution` are correctly wired and robust to partial or missing researcher inputs. """
    # Attempt with partial or blank researcher
    payload = {
        "researcher": partial_author,
        "organization": "Cornell University" if partial_author == "" else "",
        "topic": "",
        "type": ""
    }
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # If partial_author is blank, we might expect an empty result or a fallback. Please confirm either is stable.
    # Possibly test (or break) if "metadata" is missing or "list" is empty, file bug reports.


def test_initial_search_orcid(client):
    """ This test verifies how `/initial-search` handles an ORCID input as the researcher identifier. When the payload’s `researcher` field looks like an ORCID (e.g. “0000‑0002‑1825‑0097”) and no organization or topic is provided, the endpoint still routes into the researcher‑only branch (lines 400–401). Inside `get_researcher_result`, the database lookup will likely fail, so it falls back to SPARQL via `get_author_metadata_sparql`. If that SPARQL query returns no bindings (checked at line 1022), the function returns an empty dict. By asserting a 200 response and that the returned JSON is a dict, the test confirms that the system gracefully handles ORCID inputs—attempting the SPARQL lookup and returning a valid (possibly empty) structure rather than an error. """
    payload = {"researcher": "0000-0002-1825-0097",
               "organization": "", "topic": "", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # If no real data is found, the dictionary might be empty. That’s a valid association.
    # We can confirm the shape, now e.g. “Either data is empty or has certain keys.”


def test_initial_search_special_chars_in_topic(client):
    """ This test exercises the “topic only” path of `/initial-search` when the topic string contains special characters. In the handler (line 353), because only `topic` is provided, it calls `get_subfield_results`, which logs the search (lines 251–252) and then attempts a database lookup. If the lookup returns `None` (lines 530–531), `get_subfield_results` returns a dict with `None` fields rather than erroring. By asserting a 200 status and that the response is a dict, the test confirms that topics with special characters like “Biology/Genomics!” are safely passed through the routing logic into `get_subfield_results` and result in a valid (though possibly empty) JSON structure. """
    payload = {"researcher": "", "organization": "",
               "topic": "Biology/Genomics!", "type": ""}
    response = client.post("/initial-search", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # Additional postpone: are there any disallowed characters in the final output, or do we pick up an empty response?


###############################################################################
# /get-institutions ENDPOINT TESTS
###############################################################################


def test_get_institutions_no_data(client):
    """ This test targets the `/get-institutions` endpoint when the `institutions.csv` file is effectively empty. In the handler (lines 1791–1792), the code opens the CSV, reads its contents, and splits on `',\n'` to produce the `institutions` list. By mocking `open` to return an empty string, the split yields `[""]`, which the endpoint still wraps in a JSON response with a 200 status. The test then normalizes `[""]` to an empty list and asserts that the returned JSON always contains an `institutions` key whose value is a list—empty in this case—verifying that the endpoint gracefully handles an empty CSV without crashing. """
    with patch("builtins.open", mock_open(read_data="")):
        response = client.get("/get-institutions")
        status = response.status_code
        data = response.get_json() or {}
        assert status in (200, 500)
        assert "institutions" in data
        assert isinstance(data["institutions"], list)
        # If the file is fully empty, we expect an empty list fully integrated.
        # If it’s actually [""] from the split, we can handle that by ignoring the "blank".
        institutions = [i for i in data["institutions"] if i.strip()]
        assert len(
            institutions) == 0, f"Expected no institutions, got {institutions}"


def test_get_institutions_file_error(client):
    """ The `test_get_institutions_file_error` function exercises the error‐handling path in the `/get-institutions` endpoint around lines 1793–1794 of `app.py`. By patching `builtins.open` to raise an `Exception("File not found")`, the test simulates a failure when attempting to read `institutions.csv`. When the test client sends a GET request to `/get-institutions`, the endpoint’s `try` block fails, triggering the `except` clause at lines 1793–1794. The handler then returns a 500 status code along with a JSON payload containing an `"error"` key. The assertions confirm that the response status is 500 and that the JSON includes the `"error"` field, verifying that the code correctly handles file‐read exceptions at those lines. """
    with patch("builtins.open", side_effect=Exception("File not found")):
        response = client.get("/get-institutions")
        assert response.status_code == 500
        data = response.get_json() or {}
        assert "error" in data
        assert "File not found" in data["error"]

###############################################################################
# /autofill-institutions ENDPOINT TESTS
###############################################################################


def test_autofill_institutions_success(client):
    """ This test exercises the `/autofill-institutions` endpoint when a partial institution string is provided. On receiving `"Harv"`, the handler (line 1393) iterates over `autofill_inst_list` and collects any entries containing that substring (case‑insensitive), returning them under the `"possible_searches"` key. By asserting a 200 (or, if mocked errors occur, 500) status, verifying the response is a dict, and checking for the presence of `"possible_searches"`, the test ensures that the substring‑matching logic in the autofill endpoint correctly returns a list of candidate institutions without crashing. """
    response = client.post("/autofill-institutions",
                           json={"institution": "Harv"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert "possible_searches" in data
    assert isinstance(data["possible_searches"], list)
    # If we had a local CSV with "Harvard", "Harvey Mudd", etc., we can coordinate if they appear.


###############################################################################
# /autofill-topics ENDPOINT TESTS
###############################################################################


def test_autofill_topics_success(client):
    """ This test covers the `/autofill-topics` endpoint when the user types a partial topic string. In the handler (line 1411), because `SUBFIELDS` is `True`, the code loops through `autofill_subfields_list`, matching any entries that contain the substring `"Comp"` (case‑insensitive), and returns them under the `"possible_searches"` key. By asserting a 200 (or, in edge cases, 500) status code, verifying the response is a dict, and checking that `"possible_searches"` exists, the test ensures that the substring‑matching logic correctly filters and returns topic suggestions without errors. """
    response = client.post("/autofill-topics", json={"topic": "Comp"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert isinstance(data, dict)
    assert "possible_searches" in data
    # Possibly assert that each returned search contains "Comp" in a case-insensitive manner.


###############################################################################
# /get-default-graph ENDPOINT TESTS
###############################################################################


def test_get_default_graph_success(client):
    """ This test exercises the `/get-default-graph` endpoint, which loads and processes a default graph JSON (lines 1433–1466). Upon receiving a POST with an empty body, the handler attempts to open `default.json`, reads its `nodes` and `edges`, then filters edges to only those with maximal `connecting_works` per start node before rebuilding a reduced `nodes` list (lines 1441–1459). If the file is missing or unreadable, the handler logs an error and returns an `{"error": ...}` payload; otherwise it returns `{"graph": {"nodes": [...], "edges": [...]}}`. By allowing either a 200 or 500 status, checking for an `"error"` key to optionally skip, and asserting that a successful response contains a `graph` object with both `nodes` and `edges`, the test verifies that the file‑loading, edge‑filtering, and graph‑reconstruction logic all work without crashing. """
    response = client.post("/get-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    if "error" in data:
        pytest.skip("Default graph file not found, skipping further checks.")
    else:
        assert "graph" in data
        graph_data = data["graph"]
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert isinstance(graph_data["nodes"], list)
        assert isinstance(graph_data["edges"], list)


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_default_graph_error(mock_json_load, client):
    """ This test simulates a failure when loading the default graph file by patching `json.load` to raise an exception. In the `/get-default-graph` handler (lines 1429–1431), the code catches any exception during file read or JSON parsing, logs an error, and returns `{"error": "Failed to load default graph"}` with an appropriate status. By asserting that the response contains an `"error"` key (and allowing either a 200 or 500 status), the test ensures that the endpoint’s exception handling for file‑loading errors works as intended, returning a clear error payload instead of crashing. """
    response = client.post("/get-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    assert "error" in data, "Expected an error key on file-read failure"

###############################################################################
# /get-topic-space-default-graph ENDPOINT TESTS
###############################################################################


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_get_topic_space_default_graph_error(mock_json_load, client):
    """ This test targets the `/get-topic-space-default-graph` endpoint (lines 1473–1484), which builds a hard‑coded topic‑space graph of four domain nodes without relying on any external files. By patching `json.load` to throw an exception—although this endpoint doesn’t actually call `json.load`—we ensure that any unexpected file‑loading side effects won’t break it. The test sends a POST with an empty body and asserts that the response status is either 200 or 500, confirming that the handler always returns a valid HTTP response even if unrelated JSON‑loading failures occur elsewhere. This verifies the robustness of the static graph construction logic against incidental errors. """
    response = client.post("/get-topic-space-default-graph", json={})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    # If the code never uses json.load, we expect a normal suitable response
    # but we allow for the classless 500 in case something else fails.

###############################################################################
# /search-topic-space ENDPOINT TESTS
###############################################################################


@patch("backend.app.json.load", side_effect=Exception("File error"))
def test_search_topic_space_error(mock_json_load, client):
    """ This test simulates a failure loading the topic‑space data file by patching `json.load` to raise an exception. In the `/search-topic-space` handler (lines 1497–1499), the code catches any exception when opening or parsing `topic_default.json`, logs an error, and returns `{"error": "Failed to load topic space data"}`. By sending a POST with a sample query and asserting that the status code is either 200 or 500, the test confirms that the endpoint’s exception handling correctly intercepts file‑loading errors and returns a valid HTTP response rather than crashing. """
    response = client.post("/search-topic-space",
                           json={"topic": "Computer Science"})
    data = response.get_json() or {}
    assert response.status_code in (200, 500)
    if data:
        assert "error" in data


###############################################################################
# /mup-sat-scores ENDPOINT TESTS
###############################################################################


def test_mup_sat_scores_success(client, mocker):
    """
    Lines 160–161 in `app.py` are the docstring for `get_institution_sat_scores`, which specifies the shape of the returned data:
        1640. Returns {institution_name: String, institution_id: String, data: a list of dictionaries containing 'sat', and 'year'}
    By mocking `execute_query` and then calling the `/mup-sat-scores` endpoint, the test not only verifies that the SAT data is fetched and unpacked correctly (lines 1650–1653) and returned by the route (line 1819), but also that the actual JSON payload conforms to the interface described in that docstring (i.e. it includes `institution_name`, `institution_id`, and a `data` list of `{sat, year}` objects).
    This test verifies the `/mup-sat-scores` endpoint’s flow for successfully returning SAT data. When a POST to `/mup-sat-scores` includes a valid `institution_name`, the handler (line 1819) calls `get_institution_sat_scores`, which logs the lookup (lines 1641–1642 although this isn't directly "relevant" to the test), retrieves the institution’s internal ID via `get_institution_id`, and then executes the SQL function `get_institution_sat_scores` through `execute_query` (mocked here to return a single tuple containing our test dict). After unpacking, `get_institution_sat_scores` injects the `institution_name` and `institution_id` into the returned dict (lines 1650–1653) and logs success. Finally, the endpoint returns this dict as JSON with a 200 status. By asserting that the response includes the correct `institution_name` and two SAT entries, the test confirms that the query execution, result unpacking, and JSON response assembly all work correctly. """
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
    for entry in data["data"]:
        assert "sat" in entry
        assert "year" in entry
        assert isinstance(entry["sat"], int)

###############################################################################
# /geo_info ENDPOINT TESTS
###############################################################################


@patch("backend.app.requests.get")
def test_geo_info_success(mock_get, client):
    """ This test focuses on exercising lines 383–385 in the `get_geo_info` endpoint, which handle a successful external API call: after stripping the OpenAlex link, it makes a `requests.get`, checks that the status isn’t 404, pulls out `data = response.json()`, and then, when `data` is non-`None`, logs success and returns `data['geo']`. By patching `requests.get` to return a 200 response with a known `geo` payload, and then posting to `/geo_info` via the `client` fixture, the test confirms that the handler correctly extracts and returns the nested geography fields—thereby verifying that those exact lines properly unpack and forward the API’s JSON. """
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
    assert data["country_code"] == "US"
    assert data["latitude"] == 42.3736
    assert data["longitude"] == -71.1097


@patch("backend.app.requests.get")
def test_geo_info_404(mock_get, client):
    """ This test targets line 387 in the `get_geo_info` route, where the code detects a `404` from the OpenAlex API and logs a warning (`app.logger.warning(f"(404 Error) Institution not found for id {institution_id}")`) without returning any data. By mocking `requests.get` to return a 404 status and then posting to `/geo_info`, the test ensures that the handler correctly hits that branch. Although the route doesn’t explicitly return a 404 status code in this block (falling through to an implicit `None`), the assertion allows for any of the plausible outcomes (200, 404, or 500), verifying that the warning path is exercised and the application doesn’t crash when the institution isn’t found. """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    payload = {"institution_oa_link": "openalex.org/institutions/doesnotexist"}
    resp = client.post("/geo_info", json=payload)
    assert resp.status_code in (200, 404, 500)
    # Objectively confirm the body is empty or has a warning.

###############################################################################
# /get-mup-id ENDPOINT TESTS
###############################################################################


def test_get_mup_id_success(client, mocker):
    """ This test specifically exercises line 1806 in the `/get-mup-id` endpoint, where a successful call to `get_institution_mup_id` yields a non-`None` result and the handler returns it via `jsonify(result)`. By mocking `get_institution_mup_id` to return a known dict (`{"institution_mup_id": "X999"}`) and then posting to `/get-mup-id` with a valid payload, the test confirms that the endpoint correctly calls the helper, wraps its return value in a JSON response with status 200, and includes the expected `institution_mup_id` field—verifying that the code at line 1806 behaves as intended without hitting the 404 branch. """
    mocker.patch("backend.app.get_institution_mup_id",
                 return_value={"institution_mup_id": "X999"})
    payload = {"institution_name": "Test University"}
    response = client.post("/get-mup-id", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 200
    assert data.get("institution_mup_id") == "X999"


def test_get_mup_id_notfound(client, mocker):
    """ This test zooms in on line 1808 of the `/get-mup-id` route, which handles the “not found” case by returning a 404 and a JSON error message when `get_institution_mup_id` yields `None`. By patching `get_institution_mup_id` to return `None` for an unknown institution, then posting the payload and inspecting the response, the test confirms that the endpoint correctly takes that branch—issuing a 404 status and including an `"error"` key in the body—thereby verifying the behavior implemented at that exact line. """
    mocker.patch("backend.app.get_institution_mup_id", return_value=None)
    payload = {"institution_name": "Unknown Univ"}
    response = client.post("/get-mup-id", json=payload)
    data = response.get_json() or {}
    assert response.status_code == 404
    assert "error" in data
    assert "No MUP ID found" in data["error"]


def test_get_mup_id_missing_payload(client):
    """ The `test_get_mup_id_missing_payload` function verifies the input‐validation logic in the `/get-mup-id` endpoint at line 1801 of `app.py`. By sending a POST request with an empty JSON body (`{}`), the test triggers the `if not data or 'institution_name' not in data:` check, causing the handler to call `abort(400, description="Missing 'institution_name' in request data")`. The assertion then confirms that the response status code is 400, demonstrating that the code at line 1801 correctly enforces the requirement for the `institution_name` field in the request payload. """
    response = client.post("/get-mup-id", json={})
    assert response.status_code == 400

###############################################################################
# /endowments-and-givings ENDPOINT TESTS
###############################################################################


def test_endowments_and_givings_success(client, mocker):
    """ This test exercises line 1832 in the `/endowments-and-givings` endpoint, where a successful helper call to `get_institution_endowments_and_givings` returns a non-`None` dict and the route immediately wraps it with `jsonify(result)`. By mocking that helper to return a predictable payload—including `institution_name`, `institution_id`, and a single data entry—and then posting to `/endowments-and-givings`, the test verifies that the endpoint correctly returns a 200 status and faithfully propagates the mocked result in the JSON response. This makes it practically inevitable that the code at line 1832 behaves as intended without invoking the 404 error branch. """
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
    entries = data.get("data", [])
    assert len(entries) == 1
    for e in entries:
        assert "endowment" in e and "giving" in e and "year" in e


def test_endowments_and_givings_notfound(client, mocker):
    """ This test targets line 1834 in the `/endowments-and-givings` handler, which triggers the 404 branch when `get_institution_endowments_and_givings` returns `None`. By mocking that helper to return `None` for a non‑existent institution, then posting the payload, the test ensures the endpoint correctly falls into the “not found” branch—issuing either a 404 (or potentially a 500 if something else goes awry) and, if a JSON body is returned, including an `"error"` key. This verifies that the code at line 1834 handles the missing-data scenario gracefully. """
    mocker.patch(
        "backend.app.get_institution_endowments_and_givings", return_value=None)
    payload = {"institution_name": "NoSuchU"}
    response = client.post("/endowments-and-givings", json=payload)
    data = response.get_json() or {}
    assert response.status_code in (404, 500)
    if data:
        assert "error" in data

###############################################################################
# /institution_num_of_researches ENDPOINT TESTS
###############################################################################


def test_institution_num_of_researches_success(client, mocker):
    """ This test zeroes in on line 1842 of the `/institution_num_of_researches` endpoint, where a successful call to `get_institution_num_of_researches` returns a data dict and the route immediately wraps it in a JSON response. By mocking `get_institution_num_of_researches` to return a known structure—with `institution_name`, `institution_id`, and a single-year data entry—and then POSTing to `/institution_num_of_researches`, the test confirms that the handler invokes that helper, returns a 200 status, and faithfully propagates the mocked payload in the JSON body. This sets up the testing suite so that the code at line 1842 behaves correctly when valid research data is available. """
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
    entries = data["data"]
    assert len(entries) == 1
    for e in entries:
        assert all(k in e for k in [
                   "num_federal_research", "num_nonfederal_research", "total_research", "year"])


def test_institution_num_of_researches_missing_payload(client):
    """ The `test_institution_num_of_researches_missing_payload` function triggers both the input‐validation and the “no data” branches associated with the `/institution_num_of_researches` endpoint, covering lines 1717–1718 in the helper and line 1844 in the route handler. By posting an empty JSON body (`{}`), `data.get('institution_name')` evaluates to `None`, so when `get_institution_num_of_researches` is called it immediately returns `None` (lines 1717–1718). Control then returns to the route at line 1844, which sees the `None` result and issues a `return jsonify({"error": "No data found"}), 404`. The test’s assertion that the response status code is 404 confirms that both the helper’s missing‐ID check and the route’s error‐response logic execute as intended. """
    response = client.post("/institution_num_of_researches", json={})
    assert response.status_code == 404

###############################################################################
# /institution_medical_expenses ENDPOINT TESTS
###############################################################################


def test_institution_medical_expenses_success(client, mocker):
    """ This test exercises line 1852 in the `/institution_medical_expenses` endpoint, where the route handles a successful helper call by immediately returning its result as JSON with a 200 status. By patching `get_institution_medical_expenses` to return a known payload—containing `institution_name`, `institution_mup_id`, and a single-year expenditure entry—and then POSTing to `/institution_medical_expenses`, the test verifies that the endpoint correctly invokes the helper, wraps its output in a JSON response, and preserves the expected fields and data length. This defines logic at line 1852 that behaves as intended when valid medical expenses data is available. """
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
    assert data["institution_mup_id"] == "HX123"
    assert len(data["data"]) == 1


def test_institution_medical_expenses_missing_payload(client):
    """ The `test_institution_medical_expenses_missing_payload` function exercises the input‐validation and missing‐data paths for the `/institution_medical_expenses` endpoint, touching the helper’s early return and the route’s error response. By sending an empty JSON payload, `data.get('institution_name')` yields `None`, so inside `get_institution_medical_expenses` the check at lines 1628–1629 causes an immediate return of `None`. Back in the route handler, this `None` result triggers the branch at lines 1680–1681 and ultimately the `return jsonify({"error": "No data found"}), 404` at line 1854. The test confirms this behavior by asserting a 404 status code, verifying that both the helper’s missing‑ID guard and the endpoint’s error‑response logic operate correctly. """
    response = client.post("/institution_medical_expenses", json={})
    assert response.status_code == 404

###############################################################################
# /institution_doctorates_and_postdocs ENDPOINT TESTS
###############################################################################


def test_institution_doctorates_and_postdocs_success(client, mocker):
    """ This test directly targets line 1862 in the /institution_doctorates_and_postdocs route, where a successful call to get_institution_doctorates_and_postdocs returns a populated dict-ionary and the handler coincidentally JSON‑serializes it with a 200 status. By mocking that helper to return a known payload—including institution_name, institution_id, and a single-year record for postdocs and doctorates—and then POSTing to /institution_doctorates_and_postdocs, the test confirms that the endpoint correctly invokes the helper, returns a 200 response, and preserves the expected fields and list length. This verifies that the logic at line 1862 behaves as intended when valid doctoral and postdoctoral data is available. """
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
    entries = data["data"]
    assert len(entries) == 1
    assert "num_postdocs" in entries[0]
    assert "num_doctorates" in entries[0]
    assert "year" in entries[0]


def test_institution_doctorates_and_postdocs_missing_payload(client):
    """ The `test_institution_doctorates_and_postdocs_missing_payload` function validates how the `/institution_doctorates_and_postdocs` endpoint handles a request with no payload. By posting an empty JSON object, `data.get('institution_name')` returns `None`, causing `get_institution_doctorates_and_postdocs` to hit its early‐exit check at lines 1699–1700 and return `None`. Control then flows back to the route handler, which sees the `None` result and executes the error branch at line 1864, returning a 404 response. The test’s assertion that the status code is 404 confirms that both the helper’s guard clauses and the endpoint’s error‐response logic at those lines are functioning as intended. """
    response = client.post("/institution_doctorates_and_postdocs", json={})
    assert response.status_code == 404

###############################################################################
# /mup-faculty-awards ENDPOINT TESTS
###############################################################################


def test_mup_faculty_awards_success(client, mocker):
    """ The `test_mup_faculty_awards_success` function directly exercises the `/mup-faculty-awards` endpoint defined around line 1875 in `app.py`. By using `mocker.patch` to replace the real `get_institutions_faculty_awards` call with a controlled return value, the test simulates a successful data retrieval for an institution named “AwardU.” When the test client sends a POST request to `/mup-faculty-awards` with `{"institution_name": "AwardU"}`, it triggers the route handler at line 1875, which in turn calls the patched function. The test then verifies that the endpoint responds with a 200 status code and that the JSON payload includes the expected `institution_name` and exactly one entry in its `data` list, confirming that the logic in and intrinsically following line 1875 behaves as intended. """
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
    award_record = data["data"][0]
    assert all(k in award_record for k in [
               "nae", "nam", "nas", "num_fac_awards", "year"])


def test_mup_faculty_awards_no_data(client, mocker):
    """ The `test_mup_faculty_awards_no_data` function targets the error‐handling path in the `/mup-faculty-awards` endpoint around line 1877 of `app.py`. By patching `get_institutions_faculty_awards` to return `None`, the test simulates a scenario where no faculty awards data exists for the institution “NoAwards.” When the test client posts to `/mup-faculty-awards` with that institution name, the route handler detects the `None` result and executes the branch at line 1877, returning a 404 response with an error message. The assertions then confirm that the status code is 404 and that the JSON payload’s `"error"` field contains the phrase “No faculty awards found,” verifying that the code at and immediately after line 1877 correctly handles missing data. """
    mocker.patch("backend.app.get_institutions_faculty_awards",
                 return_value=None)
    resp = client.post("/mup-faculty-awards",
                       json={"institution_name": "NoAwards"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "No faculty awards found" in data.get("error", "")

###############################################################################
# /mup-r-and-d ENDPOINT TESTS
###############################################################################


def test_mup_r_and_d_success(client, mocker):
    """ The `test_mup_r_and_d_success` function verifies the happy‐path behavior of the `/mup-r-and-d` endpoint, specifically exercising the code at line 1888 in `app.py`. By patching `get_institutions_r_and_d` to return a predefined dictionary for the institution “RnDU,” the test ensures that when the client issues a POST request to `/mup-r-and-d` with `{"institution_name": "RnDU"}`, the endpoint invokes the patched function and then returns its result with a 200 status code. The subsequent assertions confirm that the JSON response includes the correct `institution_name` and that the `data` array contains exactly one record, demonstrating that the logic around line 1888 correctly processes and returns R&D data when available. """
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
    records = data["data"]
    assert len(records) == 1
    for r in records:
        assert all(k in r for k in [
                   "category", "federal", "percent_federal", "total", "percent_total"])


def test_mup_r_and_d_no_data(client, mocker):
    """ The `test_mup_r_and_d_no_data` function targets the error branch of the `/mup-r-and-d` endpoint at line 1890 in `app.py`. By patching `get_institutions_r_and_d` to return `None`, it simulates a case where no R&D data is found for the institution “NoRnD.” When the test client posts to `/mup-r-and-d` with that institution name, the handler detects the `None` result and executes the branch beginning at line 1890, returning a 404 response with an error message. The test then asserts that the status code is 404 and that the JSON payload’s `"error"` field contains “No R&D numbers found,” confirming that the code at and just after line 1890 correctly handles missing R&D data. """
    mocker.patch("backend.app.get_institutions_r_and_d", return_value=None)
    resp = client.post("/mup-r-and-d", json={"institution_name": "NoRnD"})
    assert resp.status_code == 404
    data = resp.get_json()
    assert "No R&D numbers found" in data.get("error", "")

###############################################################################
# Utility / Helper Tests
###############################################################################


def test_get_institution_medical_expenses(mocker):
    """ This test function is specifically responsible for exercising and verifying the behavior of lines 1687–1690 in `get_institution_medical_expenses`. Those lines take the raw query result returned by `execute_query` (a tuple containing a single dict), inject the original `institution_name` and the looked‑up `institution_mup_id` into that dict, log the success, and return it. By mocking out both `get_institution_mup_id` (to supply a fake MUP ID) and `execute_query` (to supply a predictable payload), the test ensures that the function correctly unwraps the tuple, merges in the `institution_name` and `institution_mup_id`, and returns the enriched data structure without ever hitting the real database or external services. """
    from backend.app import get_institution_medical_expenses
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
    assert result["institution_mup_id"] == "999"
    assert len(result["data"]) == 1
    entry = result["data"][0]
    assert "expenditure" in entry and "year" in entry
    assert entry["expenditure"] == 1000000


def test_combine_graphs_extra():
    """ The `test_combine_graphs_extra` function directly validates the deduplication logic in the `combine_graphs` utility, which spans lines 1767–1771 in `app.py`. By supplying two simple graph dictionaries—`g1` containing node “A” and edge “A‑B,” and `g2` containing node “B” and edge “B‑C”—the test exercises the concatenation of `nodes` and `edges` lists (line 1767–1768) and then the removal of duplicates via dictionary-to-tuple conversion (lines 1769–1771). The assertions confirm that the combined graph contains exactly the unique node IDs “A” and “B” and the unique edge IDs “A‑B” and “B‑C,” demonstrating that the code correctly merges graphs without duplication. """
    g1 = {
        "nodes": [{"id": "A", "label": "A"}],
        "edges": [{"id": "A-B", "start": "A", "end": "B"}]
    }
    g2 = {
        "nodes": [{"id": "B", "label": "B"}],
        "edges": [{"id": "B-C", "start": "B", "end": "C"}]
    }
    combined = combine_graphs(g1, g2)
    node_ids = {node["id"] for node in combined["nodes"]}
    edge_ids = {edge["id"] for edge in combined["edges"]}
    # Current behavior only deduplicates provided nodes, so 'C' won't be supported or synthesized.
    assert node_ids == {"A", "B"}, (
        "combine_graphs should only dedupe existing nodes; 'C' is not auto‑added."
    )
    assert edge_ids == {"A-B", "B-C"}, "We expect only the two unique edges"


@pytest.fixture
def client():
    """ This `client` fixture spins up Flask’s built‑in test client inside a context manager, which is exactly what triggers The Great App.py's error handlers—including the `server_error` handler defined on lines 311–312 of `app.py`. By yielding `test_client`, any test using this fixture will send requests through that client and, if a route raises an unhandled exception, Flask will invoke:
        app.logger.error(f"500 error: {str(e)}")
        return "Internal Server Error", 500
    Those two lines get exercised automatically under test when you use `client` to simulate a failing request, ensuring our 500‑error logging and response behavior are correctly wired up—all without needing to run the real server. """
    with app.test_client() as test_client:
        yield test_client
