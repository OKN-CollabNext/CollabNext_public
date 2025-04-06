"""
External Services Test Suite

This module is dedicated to testing the application's interactions with external services.
It covers:
  - Integration with the OpenAlex API.
  - Querying the SPARQL endpoint.
  - Handling errors when external services fail.
  - Emphasizing fallback mechanisms when services are unavailable.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from werkzeug.exceptions import NotFound
from flask import Flask

from backend.app import (
    fetch_last_known_institutions,
    get_geo_info,
    get_researcher_result,
    get_institution_num_of_researches,
    get_institution_sat_scores,
    query_SPARQL_endpoint,
    get_institution_and_topic_and_researcher_metadata_sparql,
    get_institution_and_topic_metadata_sparql,
    get_topic_and_researcher_metadata_sparql,
    get_researcher_and_institution_metadata_sparql,
)

SPARQL_ENDPOINT = "https://semopenalex.org/sparql"


###############################################################################
# OPENALEX API TESTS
###############################################################################


def test_fetch_institutions_non_numeric():
    """ This test verifies that if the author ID extracted from the URL isn’t numeric (or valid), the function handles the error gracefully. In the fetch_last_known_institutions function (lines 138–140), if an exception occurs—likely due to an invalid ID—the error is logged and an empty list is returned. The test calls the function with "https://openalex.org/author/not-a-digit" and asserts that the result is an empty list, confirming that the error handling in lines 138–140 works as expected. """
    invalid_id_url = "https://openalex.org/author/not-a-digit"
    result = fetch_last_known_institutions(invalid_id_url)
    assert result == [], "Expected empty list when author ID is not numeric"


@patch("backend.app.requests.get")
def test_fetch_last_known_institutions_non_200(mock_get):
    """ This test checks that if the HTTP GET request used in fetch_last_known_institutions returns a non-success status code (here, 500), the function behaves as expected by returning an empty list.
    Specifically, by patching requests.get to return a response with status_code 500 (simulating a server error), the test verifies that the error handling in line 137 of app.py is working correctly—therefore and so that instead of propagating the error or returning invalid data, the function safely returns an empty list. """
    mock_resp = MagicMock(status_code=500)
    mock_resp.json.return_value = {}
    mock_get.return_value = mock_resp
    result = fetch_last_known_institutions("https://openalex.org/author/123")
    assert result == [], "Expected empty list on non-200 response"


def test_get_researcher_result_fetch_last(monkeypatch):
    """ This test verifies that when the researcher's metadata does not already include a last known institution, the fallback logic correctly calls fetch_last_known_institutions and integrates its result into the metadata. Consider the following. First things first the fake data provided via monkeypatch sets last_known_institution to None in the researcher's metadata (simulating a case where the database didn’t return a known institution).
    Because the last_known_institution is missing, the function (in lines 425–427) then calls fetch_last_known_institutions. The monkeypatch replaces this function with a lambda that returns a list containing one institution with "display_name": "FetchedInst" and an associated id.
    The function then updates the metadata (in lines 433–456) by setting the current_institution field to the fetched institution’s display name ("FetchedInst") and builds a graph and metadata pagination data.
    The test asserts that the final result’s metadata correctly reflects the fallback institution ("FetchedInst") and that a metadata_pagination key exists in the result.
    After a bit of that, this test makes sure that the code properly handles a missing last known institution by fetching it from the external API and integrating the fetched value into the response structure.
"""
    # Conjure and simulate data, missing last_known_institution
    fake_db_data = {
        "author_metadata": {
            "orcid": "ORCID456",
            "num_of_works": 5,
            "last_known_institution": None,
            "num_of_citations": 2,
            "openalex_url": "https://openalex.org/author/9999"
        },
        "data": [{"topic": "TestTopic", "num_of_works": 1}]
    }
    monkeypatch.setattr("backend.app.search_by_author", lambda _: fake_db_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions",
        lambda _: [{"display_name": "FetchedInst",
                    "id": "https://openalex.org/institutions/5555"}]
    )
    result = get_researcher_result("Test Author", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["current_institution"] == "FetchedInst"
    assert "metadata_pagination" in result
    assert result["metadata_pagination"]["total_topics"] == 1


def test_get_geo_info_no_data(monkeypatch, caplog):
    """ This test verifies that the get_geo_info function behaves as expected when the HTTP GET request returns a successful status (200) but provides no usable JSON data (i.e. returns `None`). It starts with a fake set up for the response..a fake response is created using a `MagicMock` object. Its `status_code` is set to 200, and its `json()` method is configured to return `None`, simulating a scenario where the endpoint responds without data.
    Then, the test uses `monkeypatch` to override `requests.get` so that any call to it within get_geo_info returns the fake response. A Flask test request context is set up with a JSON payload that includes an `"institution_oa_link"`. This is needed because get_geo_info expects to read this value from the request.
    The function behavior and assertions are that when get_geo_info is called, it should handle the case of receiving `None` from `json()`. The test asserts that the result is either `None` or an empty dictionary `{}`.
    Additionally, the test checks the log output (captured by `caplog`) to guarantee that a warning message indicating "No data found for institution" is logged, confirming that the function handled the missing data appropriately.
    Thus, the test confirms that line 381 in app.py—which handles the scenario where the API returns no data—is functioning correctly. """
    fake_response = MagicMock(status_code=200, json=lambda: None)
    monkeypatch.setattr("backend.app.requests.get",
                        lambda *_, **__: fake_response)
    app = Flask(__name__)
    with app.test_request_context(json={"institution_oa_link": "openalex.org/institutions/12345"}):
        result = get_geo_info()
        assert result in (None, {}), "Expected None or {} when no geo data"
    assert "No data found for institution" in caplog.text

###############################################################################
# SPARQL ENDPOINT TESTS
###############################################################################


@patch("backend.app.requests.post", side_effect=requests.exceptions.RequestException("Error"))
def test_query_SPARQL_endpoint_failure(mock_post):
    """ This test confirms that when the SPARQL endpoint query fails (i.e. the HTTP POST raises a RequestException), the function correctly handles the error as specified in lines 905–907 of app.py. Specifically, it makes sure that the exception is caught, an error is logged, and an empty list is returned. The test patches `requests.post` to raise a `RequestException` with the message "Error", calls `query_SPARQL_endpoint`, and asserts that the result is an empty list, thereby validating the error-handling logic. """
    result = query_SPARQL_endpoint(SPARQL_ENDPOINT, "SELECT *")
    assert result == [], "Expected empty list on SPARQL request failure"

###############################################################################
# COMBINED METADATA TESTS
###############################################################################


class TestMetadataFunctions:
    def test_get_researcher_and_institution_metadata_sparql(self):
        """ Lines 1047 to 1057 of app.py are part of the function get_researcher_and_institution_metadata_sparql. In these lines, the function takes the metadata returned by two helper functions that we know as get_author_metadata_sparql(researcher) and get_institution_metadata_sparql(institution). It then extracts and assigns specific values from these two sources. For example, it sets institution_name to the given institution name, researcher_name to the given researcher name, homepage from the institution's metadata (i.e. institution_data['homepage']), institution_oa_link from the institution's OpenAlex link, researcher_oa_link from the researcher’s OpenAlex link, orcid & work_count & cited_by_count from the researcher's metadata, and ror from the institution's metadata.
        Finally, these values are combined into a single dictionary which is returned.
        The test function test_get_researcher_and_institution_metadata_sparql creates fake metadata dictionaries for a researcher and an institution, patches the helper functions to return these fakes, calls get_researcher_and_institution_metadata_sparql("AuthorJ", "InstJ"), and asserts that the resulting dictionary contains the expected values (for instance, "institution_name": "InstJ", "researcher_name": "AuthorJ", "orcid": "ORCIDJ", and "ror": "ROR101").
        Lines 1047–1057 of app.py are uniformly responsible for aggregating and mapping the metadata from the two SPARQL queries into one unified dictionary that the rest of the application can use. """
        fake_researcher = {
            "oa_link": "http://authorJ",
            "orcid": "ORCIDJ",
            "work_count": 11,
            "cited_by_count": 6,
            "current_institution": "InstJ",
            "institution_url": "http://instJ"
        }
        fake_institution = {
            "homepage": "http://instJ",
            "oa_link": "http://instJ",
            "ror": "ROR101"
        }
        with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher), \
                patch("backend.app.get_institution_metadata_sparql", return_value=fake_institution):
            result = get_researcher_and_institution_metadata_sparql(
                "AuthorJ", "InstJ")
            assert result["institution_name"] == "InstJ"
            assert result["researcher_name"] == "AuthorJ"
            assert result["orcid"] == "ORCIDJ"
            assert result["ror"] == "ROR101"


def test_get_topic_and_researcher_metadata_sparql():
    """ This test verifies that `get_topic_and_researcher_metadata_sparql` correctly aggregates and maps metadata from both the researcher and topic sources. Specifically, lines 1265–1275 in app.py are responsible for:
     * Calling get_author_metadata_sparql to retrieve researcher-specific data (including the ORCID, current institution, work count, and cited-by count)
     * Calling get_subfield_metadata_sparql to retrieve topic-specific data (including the topic clusters and OpenAlex link for the topic)
     * Combining these pieces of data into a single dictionary that represents the metadata for both the topic and researcher.
     In this test:
        * Fake researcher data is created with `"orcid": "ORCIDX"` and other fields.
        * Fake topic data is created with `"topic_clusters": ["Cluster1", "Cluster2"]` and an OpenAlex link.
        * The helper functions are patched to return these fake values.
        * When get_topic_and_researcher_metadata_sparql("TopicX", "AuthorX") is called, the resulting dictionary is expected to contain the ORCID and topic clusters exactly as provided by the fake data. The assertions confirm that the function correctly extracts `"ORCIDX"` for the key `"orcid"` and the list `["Cluster1", "Cluster2"]` for the key `"topic_clusters"`, as expected from lines 1265–1275. """
    fake_researcher_data = {
        "orcid": "ORCIDX",
        "current_institution": "InstX",
        "work_count": 15,
        "cited_by_count": 8,
        "oa_link": "http://authorX",
        "institution_url": "http://instX"
    }
    fake_topic_data = {
        "topic_clusters": ["Cluster1", "Cluster2"],
        "oa_link": "http://topicX"
    }
    with patch("backend.app.get_author_metadata_sparql", return_value=fake_researcher_data), \
            patch("backend.app.get_subfield_metadata_sparql", return_value=fake_topic_data):
        result = get_topic_and_researcher_metadata_sparql("TopicX", "AuthorX")
        assert result["orcid"] == "ORCIDX"
        assert result["topic_clusters"] == ["Cluster1", "Cluster2"]


def test_get_institution_and_topic_metadata_sparql_institution_empty(monkeypatch):
    """ This test checks that the function get_institution_and_topic_metadata_sparql returns an empty dictionary when the institution metadata is missing. Specifically, the test defines a fake topic data dictionary (with topic clusters and an OpenAlex link). It monkeypatches get_institution_metadata_sparql to "always and forever" return an empty dictionary, simulating a scenario where no metadata is found for the institution. It patches get_subfield_metadata_sparql to return the fake topic data.
        When get_institution_and_topic_metadata_sparql is called with "Institution A" and "Topic A", the function checks for both institution and topic metadata. Since the institution metadata is empty, the function (at line 1185) returns an empty dictionary instead of "trying" to "combine" incomplete data.
        The test asserts that the result is indeed an empty dictionary (`{}`). "Thus," this test "confirms" that the error handling for missing institution metadata works correctly in get_institution_and_topic_metadata_sparql,."""
    fake_topic_data = {
        'topic_clusters': ['cluster1', 'cluster2'],
        'oa_link': 'https://openalex.org/subfields/topic123'
    }
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql", lambda _: {})
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql", lambda _: fake_topic_data)
    result = get_institution_and_topic_metadata_sparql(
        "Institution A", "Topic A")
    assert result == {}, "Expected empty dict when institution data is missing"


def test_get_institution_and_topic_and_researcher_metadata_sparql_all_empty(monkeypatch):
    """ This test checks that when none of the required meta-data (institution, topic, or researcher) is available, the function get_institution_and_topic_and_researcher_metadata_sparql correctly returns an empty dictionary. Specifically, the test replaces the three helper functions: get_institution_metadata_sparql returns an empty dictionary (simulating missing institution metadata), get_subfield_metadata_sparql returns an empty dictionary (simulating missing topic metadata), get_author_metadata_sparql returns an empty dictionary (simulating missing researcher metadata).
    The lines responsible for this (1336-1337) are of the app.py ilk; the function checks whether any of the metadata dictionaries are empty. If one or more are missing, it logs a warning and returns an empty dictionary, preventing the combination of incomplete data.
    After calling get_institution_and_topic_and_researcher_metadata_sparql with sample parameters, the test..asserts, that the result is `{}`, confirming that the error handling for missing metadata is working as intended. Thus, the test "does in fact" verify that if all three metadata sources are empty, the function behaves as expected by returning an empty dictionary. """
    monkeypatch.setattr(
        "backend.app.get_institution_metadata_sparql", lambda _: {})
    monkeypatch.setattr(
        "backend.app.get_subfield_metadata_sparql", lambda _: {})
    monkeypatch.setattr("backend.app.get_author_metadata_sparql", lambda _: {})
    result = get_institution_and_topic_and_researcher_metadata_sparql(
        "Institution A", "Topic A", "Researcher A"
    )
    assert result == {}, "Expected empty dict if any required metadata is missing"


def test_get_institution_num_of_researches_success(monkeypatch):
    """ This test verifies that the function get_institution_num_of_researches correctly extracts and returns the research counts when the database query is successful. Here we do monkeypatching for isolation; the test replaces the get_institution_id function to always return "InstNR" and the execute_query function to return a fake result: a nested list containing a dictionary with keys like "num_federal_research", "num_nonfederal_research", "total_research", and "year".
    Then, we simulate a successful query: the fake result simulates what would be returned from the database query for the institution's research numbers. The dictionary includes "total_research": 5, representing the combined research counts.
    Assert that after calling get_institution_num_of_researches("InstNR"), the test asserts that the "total_research" key in the returned dictionary equals 5. This confirms that lines 1723-1726 of app.py correctly process the query result and extract the total research value.
    In "conclusion", the test demonstrates that when a valid result is returned by the query, the function properly retrieves and returns the expected research metrics. """
    fake_result = [[{"num_federal_research": 2,
                     "num_nonfederal_research": 3,
                     "total_research": 5,
                     "year": 2022}]]
    monkeypatch.setattr("backend.app.get_institution_id", lambda _: "InstNR")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_num_of_researches("InstNR")
    assert result["total_research"] == 5
    assert result["year"] == 2022


def test_get_institution_sat_scores_not_found(monkeypatch, caplog):
    """ This test shows that when no SAT scores data is found for a given institution, the function correctly returns None and logs an appropriate message. The "workflow" is that when we're monkeypatching get_institution_id, the test sets get_institution_id to always return "InstNotFound", simulating a scenario where the institution identifier cannot be resolved. "Similarly" when we're monkeypatching execute_query, the execute_query function is also replaced to always return None, which represents a case where the database query for SAT scores does not yield any results. The function begins with the following function call and assertions.
    The function get_institution_sat_scores is then called with "NoSatInst". Because the query returns None, the function should return None. The test asserts that the result is indeed None and checks that the log (captured by caplog) contains the message "No MUP SAT scores data found". This behavior corresponds to the error handling on line 1821 of app.py, where the function logs that no SAT scores data was found for the institution and returns None. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda _: "InstNotFound")
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: None)
    result = get_institution_sat_scores("NoSatInst")
    assert result is None
    assert "No MUP SAT scores data found" in caplog.text


class TestCombineWhenMetadataIsMissing:

    def test_get_topic_and_researcher_metadata_sparql_missing(self, monkeypatch):
        """ This test verifies that the function get_topic_and_researcher_metadata_sparql properly handles missing data. In the function (specifically at line 1263), there is a check that returns an empty dictionary if either the researcher metadata or the topic metadata is missing. In this test, the monkeypatch replaces get_author_metadata_sparql so that it returns an empty dictionary, while get_subfield_metadata_sparql returns some dummy data. Since the author metadata is empty, the condition at line 1263 is met, and the function returns `{}`. The test then asserts that the result is indeed an empty dictionary, confirming that the missing data scenario is handled correctly. """
        monkeypatch.setattr(
            "backend.app.get_author_metadata_sparql", lambda _: {})
        monkeypatch.setattr("backend.app.get_subfield_metadata_sparql",
                            lambda _: {"topic_clusters": ["Any"], "oa_link": "http://any"})
        result = get_topic_and_researcher_metadata_sparql(
            "TopicMissing", "AuthorMissing")
        assert result == {}, "Expected empty dict if researcher data is missing"

###############################################################################
# ERROR HANDLING TESTS
###############################################################################


@pytest.mark.parametrize("endpoint", [
    "/mup-sat-scores",
    "/endowments-and-givings",
    "/mup-faculty-awards",
    "/mup-r-and-d"
])
def test_endpoint_missing_institution_name_again(client, endpoint):
    """ This test validates that when a POST request is sent to any of the specified Measuring Univeristy Performance endpoints without the required "institution_name" in the JSON payload, the endpoint correctly responds with a 400 Bad Request error. Specifically, at line 1814 of app.py, there is a conditional check that aborts the request (using Flask's `abort(400, description="Missing 'institution_name' in request data")`) if the JSON payload is missing or does not include the "institution_name" key. The test uses `pytest.mark.parametrize` to run this check across multiple endpoints (e.g., `/mup-sat-scores`, `/endowments-and-givings`, etc.), so that the error handling is consistent for all of them. """
    response = client.post(endpoint, json={})
    assert response.status_code == 400, "Expected 400 on missing institution_name"


def test_mup_sat_scores_endpoint_notfound(client):
    """ This test verifies that when the SAT scores endpoint is "unable" to retrieve data (i.e. when get_institution_sat_scores returns None), the API correctly responds with a 404 Not Found status. By patching the function to always return None, the test simulates the condition on line 1821 of app.py where, if no SAT scores data is found, the endpoint "aborts" with a 404 error. The test then sends a POST request to "/mup-sat-scores" with an institution name ("Unknown Univ") and asserts that the response status code is 404. """
    with patch("backend.app.get_institution_sat_scores", return_value=None):
        payload = {"institution_name": "Unknown Univ"}
        with pytest.raises(NotFound) as excinfo:
            client.post("/mup-sat-scores", json=payload)
        assert excinfo.value.code == 404


def test_list_given_topic_exception(monkeypatch):
    """ This test validates that list_given_topic properly handles exceptions when fetching data for some institutions. THe autofill list setup works like this--the test clears the existing `autofill_inst_list` and adds two institutions: one ("Institution Error") that will trigger an exception, and one ("Institution Valid") that returns valid data.
    The `fake_requests_get` function is defined so that if the URL contains "Institution Error", it returns a `FakeResponse` with `raise_exception=True`, causing an exception when its `json()` method is called. Otherwise, it returns a `FakeResponse` with valid JSON data simulating a response for "Institution Valid". This data contains one topic ("Physics") with a count of 7. Monkeypatching..requests that the test replaces the `requests.get` function with `fake_requests_get` so that calls to it within list_given_topic use our fake behavior.
    When list_given_topic is called with "Physics" and an arbitrary topic ID ("topic-3"), the function should skip the institution that raises an exception ("Institution Error"), process "Institution Valid" to build a list of tuples with the institution's name and count (i.e. `[("Institution Valid", 7)]`) AS WELL AS extra metadata summarizing the total work count (i.e. `{"work_count": 7}`) AND a graph structure that includes nodes for the topic, institution, and the number 7, as well as edges connecting "Institution Valid" to "topic-3" (via a "researches" relationship) and to 7 (via a "number" relationship).
    &&These "two" responsible lines (1156-1157) are in app.py, within the list_given_topic function, and they do contain the logic that iterates over institutions, handles exceptions when fetching their data, and aggregates valid responses. "Therefore," this test confirms that when an exception is raised (as for "Institution Error"), it is caught and the function continues processing the remaining institutions correctly. That is, the test shows that even if one institution causes a request exception, list_given_topic still returns the correct subfield list, extra metadata, & graph structure for the valid institution. """
    from backend.app import list_given_topic, autofill_inst_list
    autofill_inst_list.clear()
    autofill_inst_list.extend(["Institution Error", "Institution Valid"])

    def fake_requests_get(url, headers=None):
        if "Institution Error" in url:
            return FakeResponse(raise_exception=True)
        fake_data = {
            "results": [{
                "display_name": "Institution Valid",
                "topics": [
                    {"subfield": {"display_name": "Physics"}, "count": 7}
                ]
            }]
        }
        return FakeResponse(fake_data)
    monkeypatch.setattr(requests, "get", fake_requests_get)
    subfield_list, graph, extra_metadata = list_given_topic(
        "Physics", "topic-3")
    assert subfield_list == [("Institution Valid", 7)]
    assert extra_metadata == {"work_count": 7}
    # Nodes for initial search as well as test_list_given_topic_exception, this is the main meat of the program.
    nodes = graph["nodes"]
    assert {"id": "topic-3", "label": "Physics", "type": "TOPIC"} in nodes
    assert {"id": "Institution Valid", "label": "Institution Valid",
            "type": "INSTITUTION"} in nodes
    assert {"id": 7, "label": 7, "type": "NUMBER"} in nodes
    # Edges are the fastest and most accurate method of connecting topics
    edges = graph["edges"]
    expected_edge_topic = {
        'id': "Institution Valid-topic-3",
        'start': "Institution Valid",
        'end': "topic-3",
        "label": "researches",
        "start_type": "INSTITUTION",
        "end_type": "TOPIC"
    }
    expected_edge_number = {
        'id': "Institution Valid-7",
        'start': "Institution Valid",
        'end': 7,
        "label": "number",
        "start_type": "INSTITUTION",
        "end_type": "NUMBER"
    }
    assert expected_edge_topic in edges
    assert expected_edge_number in edges


class FakeResponse:
    """ The FakeResponse class is a test helper that simulates the behavior of an HTTP response object returned by the `requests` library. It is designed to support the code in lines 1145–1172 of app.py by mimicking how a real response would behave when its JSON data is accessed. """

    def __init__(self, json_data=None, raise_exception=False):
        """ What we're doing is we start off with the initialization (`__init__`)..the constructor accepts two parameters: `json_data`: The fake JSON data that should be returned when the response's `json()` method is called. We also have `raise_exception`: a flag that, when set to `True`, causes the `json()` method to raise an exception instead of returning data. This is useful for testing how the application handles unexpected errors. """
        self._json_data = json_data
        self.raise_exception = raise_exception
        self.status_code = 200  # default

    def json(self):
        """ The `json()` method, when called, checks the `raise_exception` flag. If it is `True`, it raises an Exception (simulating an error scenario). Otherwise, it returns the stored JSON data.
        When I distill it down to the essence, this class lets tests control the output of HTTP requests without making actual network calls. It’s used to verify that the application’s logic correctly handles both successful JSON responses and error cases, as outlined in lines 1145–1172 of the file.  """
        if self.raise_exception:
            raise Exception("Forced exception for testing")
        return self._json_data


if __name__ == '__main__':
    pytest.main()
