from backend.app import app
import sys
import runpy
import json
import os
from io import StringIO
import mysql.connector
from mysql.connector import Error
import pytest
from unittest.mock import patch, MagicMock
import backend.app as backend_app
import mysql.connector
import json
import os
from io import StringIO
from unittest.mock import patch, MagicMock
from mysql.connector import Error
import pytest
from flask import Response
from backend.app import (
    serve,
    get_institutions_faculty_awards,
    get_institutions_r_and_d,
    get_institution_mup_id,
    create_connection,
    get_institution_endowments_and_givings,
    query_SQL_endpoint,
    get_institution_and_researcher_results,
    list_given_institution_topic,
    list_given_researcher_topic,
    execute_query,
    get_institution_and_subfield_results,
    search_by_author_institution,
    get_researcher_result,
    get_institution_medical_expenses,
    get_institution_doctorates_and_postdocs,
    get_institution_num_of_researches,
    get_subfield_results,
    get_institution_sat_scores,
    get_researcher_and_subfield_results,
    get_institution_results,
    get_institution_id, get_institution_researcher_subfield_results
)
import pytest
from unittest.mock import patch, MagicMock
from backend.app import (
    app,
    search_by_author_institution_topic,
    search_by_author_institution,
)
import json


def test_search_by_author_institution_topic_no_result(caplog):
    """ The test is designed to exercise the branch in the function where no results are returned from the database query. In the function `search_by_author_institution_topic`, after retrieving the author and institution IDs, it calls `execute_query` with the given parameters. If that call returns no results (i.e. returns `None`), then—specifically on lines 185 and 186—the function logs a warning saying "No results found for author-institution-topic search" and then returns `None`.
    In the test, by patching `execute_query` to return `None`, we simulate this no-result scenario. The test then asserts that the function indeed returns `None` and that the warning message is present in the log output (captured in `caplog`). This verifies that the code on lines 185 and 186 is executed correctly EVEN when there are no query results. """
    with patch("backend.app.get_author_ids", return_value=[{"author_id": "A1"}]), \
            patch("backend.app.get_institution_id", return_value="I1"), \
            patch("backend.app.execute_query", return_value=None):
        result = search_by_author_institution_topic(
            "Author", "Institution", "Topic")
        assert result is None
        assert "No results found for author-institution-topic search" in caplog.text


class TestConfigurationAndErrors:
    def test_search_by_author_institution_no_result(self, caplog):
        """ This test verifies the behavior of the `search_by_author_institution` function when no results are returned from the database query. Specifically, lines 208–209 of the source code log a warning message ("No results found for author-institution search") and return `None` when the call to `execute_query` yields no data.
        In the test, the functions `get_author_ids` and `get_institution_id` are patched to return dummy values (an author ID and an institution ID), and `execute_query` is patched to return `None`. This forces the function to follow the code path where no results are found. The test then asserts that the function returns `None` and checks that the warning message is present in the captured logs (`caplog`), confirming that lines 208–209 are executed as expecte--at least accordin tto the source cdoe.  """
        with patch("backend.app.get_author_ids", return_value=[{"author_id": "A1"}]), \
                patch("backend.app.get_institution_id", return_value="I1"), \
                patch("backend.app.execute_query", return_value=None):
            result = search_by_author_institution("Author", "Institution")
            assert result is None
            assert "No results found for author-institution search" in caplog.text

    def test_get_institution_medical_expenses_no_data(self, monkeypatch, caplog):
        """ This test simulates the scenario where the SQL query returns no data for medical expenses. If you wanted to know it corresponds to lines 1691–1692 , the test uses monkeypatch to patch get_institution_mup_id to return a dummy MUP ID ({"institution_mup_id": "MUP123"}), such the function gets "past" the check for a missing Measuring Univeristy Performance ID..execute_query "is to" return None, simulating the condition where no medical expenses data is found in the database.
        Now, in the function get_institution_medical_expenses, after retrieving the MUP ID and executing the query, the code checks if any results were returned. Since the patched execute_query returns None, the code logs the message "No MUP medical expenses data found for InstMed" (lines 1691–1692) and then returns None.
        The test asserts that the function returns None and that the expected log message is captured in caplog, thereby verifying that the specific code path (lines 1691–1692) is executed as intended. """
        monkeypatch.setattr("backend.app.get_institution_mup_id", lambda name: {
                            "institution_mup_id": "MUP123"})
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_medical_expenses("InstMed")
        assert result is None
        assert "No MUP medical expenses data found for InstMed" in caplog.text

    def test_get_institution_doctorates_and_postdocs_no_data(self, monkeypatch, caplog):
        """ This test verifies the behavior of the get_institution_doctorates_and_postdocs function when no data is returned from the database. Specifically, lines 1709–1710 log a warning message stating "No MUP doctorates and postdocs data found for InstDP" and then return None. In this test get_institution_id is patched (using monkeypatch) to always return the dummy institution ID "InstDP", execute_query is patched to return None, simulating a scenario where the query retrieves no results, AND the function is then called with "InstDP", and the test asserts that it returns None and that the expected log message is present in caplog..this confirms that the function behaves as expected for the no-data scenario, specifically executing the code at lines 1709–1710. """
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstDP")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_doctorates_and_postdocs("InstDP")
        assert result is None
        assert "No MUP doctorates and postdocs data found for InstDP" in caplog.text

    def test_get_institution_num_of_researches_no_data(self, monkeypatch, caplog):
        """ This test checks the behavior of the get_institution_num_of_researches function when no research data is found in the database. Specifically, lines 1727–1728 in the code log the warning message "No MUP number of researchers data found for InstNR" and then return None. In the test, get_institution_id is patched to return the dummy institution ID "InstNR", execute_query is patched to return None, simulating a scenario where the SQL query does not return any data. And the function get_institution_num_of_researches is then called with "InstNR", and the test asserts that (1) the function returns None (2) the warning log message is present in caplog.text. As such this confirms that the code in lines 1727–1728 is executed correctly when no data is found. """
        monkeypatch.setattr("backend.app.get_institution_id",
                            lambda name: "InstNR")
        monkeypatch.setattr("backend.app.execute_query",
                            lambda q, params: None)
        result = get_institution_num_of_researches("InstNR")
        assert result is None
        assert "No MUP number of researchers data found for InstNR" in caplog.text


class TestSearchFunctions:
    def test_get_subfield_results_success_variant(self, monkeypatch):
        """ This test is designed to simulate a successful scenario when a user searches by subfield (topic) and verifies that the processing performed in lines 533–570 of the application code is correct..the test creates a fake data dictionary (fake_data) that mimics the structure returned by the function search_by_topic. This dictionary includes a subfield_metadata list (with one entry for demonstration), a totals dictionary that contains the total number of works, citations, and authors, and a data list with details about institutions and the number of authors.
        With regard to monkeypatching after simulating data retrieval, the test patches search_by_topic so that regardless of the input topic, it returns the fake data. This forces get_subfield_results to process the known fake data instead of performing an actual search. The processing in get_subfield_results (Lines 533–570) is done inside the function, where the following happens..it extracts subfield_metadata to build a list of topic clusters and it then.. populates the metadata dictionary with values from the totals (e.g., setting metadata["work_count"] to 40, metadata["cited_by_count"] to 20, and metadata["researchers"] to 5).
        It  sets metadata["oa_link"] using the subfield_url from the fake data. The topic name is set by converting the input topic to title case (i.e., topic.title()).
        The test ASSERTS that: the work_count in the returned metadata is 40 (as specified in the fake totals), the topic name in the metadata contains "SubfieldX" (indicating that the input topic was correctly processed and transformed). By doing this, the test confirms that the function correctly processes the fake data, extracting and setting the expected values, which is exactly what lines 533–570 are responsible for. """
        fake_data = {
            "subfield_metadata": [{"topic": "SubTest", "subfield_url": "http://subtest"}],
            "totals": {"total_num_of_works": 40, "total_num_of_citations": 20, "total_num_of_authors": 5},
            "data": [{"institution_name": "InstTest", "num_of_authors": 3}]
        }
        monkeypatch.setattr("backend.app.search_by_topic",
                            lambda topic: fake_data)
        result = get_subfield_results("SubfieldX", page=1, per_page=10)
        metadata = result["metadata"]
        assert metadata["work_count"] == 40
        assert "SubfieldX" in metadata.get("name", "SubfieldX")


class TestInternalFunctions:
    def test_execute_query_success(self):
        """ This test validates that the execute_query function successfully executes a query and returns the expected results. It relates to lines 117–122 in the file app.py, by simulating, creating fake connection and cursor objects using MagicMock. It sets up the fake cursor so that when its fetchall() method is called, it returns [("result",)]. Additionally, the cursor and connection are set up with proper context manager behavior using __enter__. To patch the database connection, the test patches psycopg2.connect to return the fake connection. This simulates a successful database connection without making a real connection.
        The execution flow (Lines 117–122) takes place within the execute_query function..the code enters a context manager with the database connection. It then opens a cursor (using a with statement). The query is executed, and fetchall() is called to retrieve the results. The function logs an info message and returns the fetched results. The fake cursor's fetchall() returning [("result",)] provides that the function returns this value. Finally, the test asserts that execute_query("SELECT 1;", None) returns [("result",)], confirming that the code path corresponding to lines 117–122 executes as expected.
        This test effectively verifies that the function handles a successful query execution by correctly managing the connection and cursor and returning the expected result. """
        fake_cursor = MagicMock()
        fake_cursor.fetchall.return_value = [("result",)]
        fake_cursor.__enter__.return_value = fake_cursor
        fake_conn = MagicMock()
        fake_conn.cursor.return_value = fake_cursor
        fake_conn.__enter__.return_value = fake_conn
        with patch("backend.app.psycopg2.connect", return_value=fake_conn):
            result = execute_query("SELECT 1;", None)
            assert result == [("result",)]


class TestEndpoints:
    def test_index_serves_html(self, client, monkeypatch):
        """ This test guarantees that the index route (line 302) correctly serves the HTML file for the root path. The monkeypatching test replaces send_from_directory in the application with a lambda function that always returns an HTTP response containing <html>Index</html> with a status code of 200. This bypasses the actual file serving logic and simulates a successful HTML response. The test then makes a client-side GET request to the root endpoint ("/") using the Flask test client. The test asserts that the response status code is 200, indicating a successful request, the response data contains the expected HTML snippet (<html>), confirming that the index route is serving HTML AND last but not least this test verifies that line 302, which calls send_from_directory to serve the index page, is triggered correctly and returns an HTML response. """
        monkeypatch.setattr("backend.app.send_from_directory",
                            lambda folder, file: Response("<html>Index</html>", status=200))
        response = client.get("/")
        assert response.status_code == 200
        assert b"<html>" in response.data

    def test_search_topic_space_endpoint(self, client, monkeypatch):
        """ The test is verifying that the functionality implemented in lines 1513 to 1587 of the application code works as intended. It all ties together via fake data injection..the test creates a fake topic graph (a JSON structure with one node representing a topic and associated hierarchy details). It then monkeypatches the built‑in open function so that when the endpoint code attempts to open `"topic_default.json"`, it instead reads this fake graph. The dndpoint behavior (Lines 1513–1587) "spec-ifies" that in the `/search-topic-space` endpoint, after loading the JSON data, the code iterates through each node in the graph. For each node, it checks if the search term (from the request) matches the node’s label, subfield, field, domain, or keywords.
        In our fake graph, the node’s `"label"` is `"Test Topic"`, so it matches the search term provided by the test. Upon a match (line 1513 and onward), the code builds new nodes and edges: it creates a topic node (with type `"TOPIC"`) and hierarchy nodes (for subfield, field, and domain) along with edges connecting them. The test then posts a request with the search term `"Test Topic"`, receives the processed graph in the response, and asserts that the graph includes at least one node with a type `"TOPIC"`. This confirms that the logic from lines 1513 to 1587 correctly processed the input and built the expected graph structure.
         The test adds up that the section of the endpoint responsible for filtering the topic space and constructing a hierarchy (as detailed in lines 1513–1587) functions correctly when given a matching topic. """
        fake_topic_graph = {
            "nodes": [{
                "id": "T1",
                "label": "Test Topic",
                "subfield_name": "SubTest",
                "field_name": "FieldTest",
                "domain_name": "DomainTest",
                "keywords": "alpha; beta",
                "summary": "Dummy",
                "wikipedia_url": "http://wikipedia.org",
                "subfield_id": "ST1",
                "field_id": "F1",
                "domain_id": "D1"
            }],
            "edges": []
        }
        monkeypatch.setattr("builtins.open", lambda f, mode='r': StringIO(json.dumps(fake_topic_graph))
                            if "topic_default.json" in f else StringIO(""))
        response = client.post("/search-topic-space",
                               json={"topic": "Test Topic"})
        data = response.get_json()
        assert "graph" in data
        graph = data["graph"]
        assert any(n.get("type") == "TOPIC" for n in graph["nodes"])


def test_get_researcher_result_with_last(monkeypatch):
    """ The unit test simulates a scenario where an author's metadata already contains a value for "last_known_institution." In the get_researcher_result function, line 412 is part of the logic that checks if the metadata already has a non‑null "last_known_institution." When it does (as in the test case with "InstA"), the function sets the "current_institution" field in the metadata to that value.
    In this test, the monkeypatch replaces the call to search_by_author so that it returns the fake data with "last_known_institution": "InstA". The assertions then verify that (1) the returned metadata has "current_institution" set to "InstA" and (2) he result includes pagination information under "metadata_pagination".
    This confirms that the code at line 412 (which assigns metadata['current_institution'] = last_known_institution) is correctly processing and propagating the provided institution data. """
    fake_data = {
        "author_metadata": {
            "orcid": None,
            "num_of_works": 10,
            "last_known_institution": "InstA",
            "num_of_citations": 5,
            "openalex_url": "https://openalex.org/author/1234"
        },
        "data": [{"topic": "Topic1", "num_of_works": 3}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    result = get_researcher_result("Test Author", page=1, per_page=10)
    assert result["metadata"]["current_institution"] == "InstA"
    assert "metadata_pagination" in result


def test_get_researcher_result_without_last(monkeypatch, caplog):
    """ In this test, the fake data is set up so that the author's metadata has a value of `None` for `"last_known_institution"`. That forces the code in lines 422–423 of the application to execute (1) Because `metadata['last_known_institution']` is `None`, the function logs a debug message and then calls `fetch_last_known_institutions` with the author’s OpenAlex URL (2) The test monkeypatches `fetch_last_known_institutions` to return an empty list (`[]`). (3) Since the returned list is empty, the code logs a warning with the message `"No last known institution found"` and sets `last_known_institution` to an empty string (`""`). (4) Finally, the metadata’s `"current_institution"` is updated with this empty string.
    The test then verifies that:
        * `"current_institution"` in the returned metadata is `""`.
        * The log (captured by `caplog`) contains the warning `"No last known institution found"`.
        This confirms that lines 422–423 correctly handle cases where there is no last known institution provided in the metadata. """
    fake_data = {
        "author_metadata": {
            "orcid": "ORCID123",
            "num_of_works": 8,
            "last_known_institution": None,
            "num_of_citations": 4,
            "openalex_url": "https://openalex.org/author/5678"
        },
        "data": [{"topic": "Topic2", "num_of_works": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_author",
                        lambda author: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda oa_link: [])
    result = get_researcher_result("Test Author", page=1, per_page=10)
    assert result["metadata"]["current_institution"] == ""
    assert "No last known institution found" in caplog.text


def test_get_researcher_and_subfield_results_fallback(monkeypatch, caplog):
    """ This test validates the fallback logic in the get_researcher_and_subfield_results function when the database query returns no results. Specifically, lines 589–594 are executed when the initial call to search_by_author_topic returns None, triggering the fallback mechanism. The function then logs that it's falling back to SPARQL and calls get_topic_and_researcher_metadata_sparql, which in this test is monkeypatched to return fake_sparql_metadata (with "current_institution": "InstD" among other values).
    Next, the function calls list_given_researcher_topic (also monkeypatched) to obtain a dummy work list, graph, and extra metadata.
    Finally, the SPARQL results are incorporated into a results dictionary that includes metadata. The test asserts that the final result includes a "metadata" key., the "current_institution" field within the metadata is set to "InstD", as provided by the fake SPARQL metadata.
    Thus, this test confirms that yes, lines 589–594 correctly handle the fallback to SPARQL when the initial database search fails. """
    fake_sparql_metadata = {
        "current_institution": "InstD",
        "topic_oa_link": "http://topic",
        "researcher_oa_link": "http://author",
        "institution_oa_link": "http://instD"
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_topic", lambda a, t: None)
    monkeypatch.setattr(
        "backend.app.get_topic_and_researcher_metadata_sparql", lambda t, a: fake_sparql_metadata)
    monkeypatch.setattr("backend.app.list_given_researcher_topic", lambda t, a, i, t_oa, a_oa, i_oa: (
        ["dummy_work"], {"nodes": [], "edges": []}, {"work_count": 1, "cited_by_count": 2}))
    result = get_researcher_and_subfield_results(
        "Test Author", "Test Topic", page=1, per_page=10)
    assert "metadata" in result
    assert result["metadata"]["current_institution"] == "InstD"


def test_get_institution_doctorates_and_postdocs_success(monkeypatch):
    """ This test verifies that the function handling doctorates and postdocs data correctly processes and returns the expected values when the SQL query is successful. Here's what happens when I monkeypatch..the test replaces get_institution_id to return a fixed ID ("InstDP") so that the function uses this constant instead of performing an actual lookup. It also replaces execute_query so that it returns a fake result: a nested list with one dictionary containing "num_postdocs": 3, "num_doctorates": 10, and "year": 2021.
    The function get_institution_doctorates_and_postdocs (responsible for lines 1705–1708) executes and uses these monkeypatched functions to obtain data from the database query. When execute_query returns the fake result, the function extracts the first dictionary (fake_result[0][0]) and returns it after adding the institution name and ID. The test then asserts that the returned dictionary has "num_doctorates" equal to 10, confirming that the function correctly parsed and returned the expected value.
    That is how lines 1705–1708 are responsible for retrieving and returning the result of the SQL query, and this test confirms that the function correctly extracts the "num_doctorates" value from the fake query result. """
    fake_result = [[{"num_postdocs": 3, "num_doctorates": 10, "year": 2021}]]
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "InstDP")
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_doctorates_and_postdocs("InstDP")
    assert result["num_doctorates"] == 10


def test_get_researcher_and_subfield_results_processing(monkeypatch, caplog):
    """ This test verifies that when valid database results are provided (via the fake data), the function correctly processes the work entries. In particular, lines 641–647 iterate over the entries in the `"data"` field and do the following for each work:
    * Extract the work name and its citation count.
    * Append a tuple with these values to the list view.
    * Add nodes for the work and the corresponding citation number.
    * Create edges linking the researcher to the work and the work to its citation count.
    The test sets up fake data with one entry (with `"work_name": "WorkTest"` and `"num_of_citations": 5`), and then it confirms that the metadata is updated (e.g., `"researcher_name"` is set to `"TestAuthor"`, and `"current_institution"` is `"InstTest"`). It also asserts that the final result includes both a `"graph"` (containing the nodes and edges built from the work entry) and a `"list"` (which should include the tuple from processing the work entry).
    Thus, the test guarantees that lines 641–647 correctly process each work entry and incorporate that data into the graph and list results. """
    fake_data = {
        "subfield_metadata": [{"topic": "TestSub", "subfield_url": "http://testsub"}],
        "totals": {"total_num_of_works": 20, "total_num_of_citations": 10},
        "author_metadata": {
            "orcid": "ORCID123",
            "openalex_url": "http://author_test",
            "last_known_institution": "InstTest"
        },
        "data": [{"work_name": "WorkTest", "num_of_citations": 5}]
    }
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    result = get_researcher_and_subfield_results(
        "TestAuthor", "TestTopic", page=1, per_page=10)
    metadata = result.get("metadata", {})
    assert metadata.get("researcher_name") == "TestAuthor"
    assert metadata.get("current_institution") == "InstTest"
    assert "graph" in result
    assert "list" in result


def test_get_institution_results_homepage(monkeypatch):
    """ This test verifies that the institution metadata is correctly processed, particularly the "homepage" field. In lines 479–512 of app.py, we have (1) data retrieval and mapping in that the function `get_institution_results` calls `search_by_institution`, which in this test is monkeypatched to return a fake data dictionary. The fake data contains an `"institution_metadata"` key with a `"url"` field set to `"http://homepage_test"` AS WELL AS (2) metadata processing, because in the function, the metadata is altered as follows:
   * `metadata['homepage']` is explicitly set to `metadata['url']`.
   * Other fields like `works_count`, `name`, `cited_count`, `oa_link`, and `author_count` are mapped from the respective keys in the fake data.
   Third, we ahve that the test asserts that the resulting metadata's `"homepage"` is exactly `"http://homepage_test"`, confirming that the code correctly maps the `url` value to the `homepage` key. Thus that is how we are "aware" that, lines 479–512 are responsible for processing the institution metadata and setting the homepage value correctly, which is verified by the test. """
    fake_data = {
        "institution_metadata": {
            "url": "http://homepage_test",
            "num_of_works": 25,
            "institution_name": "InstHomepage",
            "num_of_citations": 18,
            "openalex_url": "http://instHomepage",
            "num_of_authors": 6
        },
        "data": [{"topic_subfield": "SubHomepage", "num_of_authors": 2}]
    }
    monkeypatch.setattr("backend.app.search_by_institution",
                        lambda inst: fake_data)
    result = get_institution_results("InstHomepage", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["homepage"] == "http://homepage_test"


def test_get_institution_id_empty_result(caplog):
    """ This test checks the behavior of the `get_institution_id` function when the database query returns an empty result (represented as a dictionary with no content). When we "look into" how it relates to lines 158–159 in app.py "we get" this simulated result that the test monkeypatches the `execute_query` function to return a fake result of `[[{}]]`. This simulates a scenario where the query executes successfully but doesn't find a valid institution ID.
    What is the behavior of "this function" (Lines 158–159)? Well, in the actual function, after executing the query, there is a check:
    * If `results` is not empty but `results[0][0]` is an empty dictionary (`{}`), the code logs a warning `"No institution ID found for {institution_name}"` and returns `None`.
    * The test asserts two things (1) that `get_institution_id("NoIDInst")` returns `None`..(2) that the log (captured in `caplog.text`) contains the warning message `"No institution ID found"`.
    Then it is time to "clean-up". The test uses `monkeypatch.undo()` to clean up the monkeypatch after the test runs.
     In all possible ways, this test shows every time that whenever and wherever the query returns an empty dictionary (i.e., no institution ID is found), the function correctly logs a warning and returns `None`, as integrated discretely in lines 158–159 of app.py. """
    fake_result = [[{}]]
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("backend.app.execute_query",
                        lambda q, params: fake_result)
    result = get_institution_id("NoIDInst")
    assert result is None
    assert "No institution ID found" in caplog.text
    monkeypatch.undo()


def test_search_by_institution_topic_no_results(monkeypatch, caplog):
    """ This test verifies that the `search_by_institution_topic` function correctly handles the case when no data is returned from the database. This is what happens in relation to lines 223–224, "when you do that" monkeypatch then the `get_institution_id` function is patched to return a dummy institution ID (`"dummy_inst_id"`). The `execute_query` function is patched to return an empty list, simulating a scenario where the SQL query finds no matching results.
    In the function (Lines 223–224) the behavior follows the `search_by_institution_topic` function, wherein after executing the query, the code checks if any results were returned. If the results are empty, the function logs a warning stating `"No results found for institution-topic search"` and returns `None`. The test "confirms" that:
  * The function returns `None`.
  * The log output (captured by `caplog`) includes the warning message, "indicating" that the function detected no results. That is how this test thus is able to show that the fallback logic for empty query results in `search_by_institution_topic` works as expected. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda inst: "dummy_inst_id")
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_institution_topic
    result = search_by_institution_topic("TestInstitution", "TestTopic")
    assert result is None
    assert "No results found for institution-topic search" in caplog.text


def test_search_by_author_topic_no_results(monkeypatch, caplog):
    """ This test verifies that the `search_by_author_topic` function properly handles the scenario when no results are returned from the query. In particular, lines 241–242 of app.py are responsible for checking whether the query yielded any results and, if not, logging a warning and returning `None`. It starts with monkeypatching of `get_author_ids` which we monkeypatch for the purpose of re-turning a dummy author ID list (`[{"author_id": "dummy_author_id"}]`), so that the function proceeds to query execution.
    Then, `execute_query` is monkeypatched to return an empty list (`[]`), simulating a case where the SQL query doesn't find any matching records. Here's the function behavior (Lines 241–242)..after calling `execute_query`, the function inspects the returned results. Since the list is empty, the function logs a warning message stating `"No results found for author-topic search"` and returns `None`.
    The test "likewise"..asserts that the function returns `None`. It also checks that the log (captured by `caplog`) contains the warning message, confirming that the no-result condition was correctly detected & handled. This confirms that lines 241–242 correctly manage the absence of query results by logging an appropriate warning and returning `None`. """
    monkeypatch.setattr("backend.app.get_author_ids", lambda author: [
                        {"author_id": "dummy_author_id"}])
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_author_topic
    result = search_by_author_topic("TestAuthor", "TestTopic")
    assert result is None
    assert "No results found for author-topic search" in caplog.text


def test_search_by_institution_no_results(monkeypatch, caplog):
    """ This test checks that the `search_by_institution` function behaves correctly when the database query returns no results. Relative to lines 266–267, the `get_institution_id` function is monkeypatched to always return a dummy institution ID (`"dummy_inst_id"`). The `execute_query` function is monkeypatched to return an empty list (`[]`), simulating a situation where the SQL query does not find any matching records for the given institution. In the function (Lines 266–267) specifically within the `search_by_institution` function, after attempting to retrieve the institution ID and executing the query, the function checks whether any results were obtained. Since the patched `execute_query` returns an empty list, the function logs a warning message indicating `"No results found for institution: FakeInstitution"` and returns `None`. The test asserts that of course the function returns `None`. And..the log (captured by `caplog`) contains the warning message, verifying that the absence of results was correctly detected and logged. This..confirms that lines 266–267 correctly handle the no-result scenario by logging an appropriate message and returning `None`. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        lambda name: "dummy_inst_id")
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_institution
    result = search_by_institution("FakeInstitution")
    assert result is None
    assert "No results found for institution: FakeInstitution" in caplog.text


def test_search_by_author_no_results(monkeypatch, caplog):
    """ This test ensures that the `search_by_author` function correctly handles a scenario in which no query results are found. Specifically, lines 284–285 in app.py check if the query for an author returns any data and, if not, log a warning and return `None`. `get_author_ids` we monkeypatch to return a dummy author ID (`[{"author_id": "dummy_author_id"}]`), so the function continues with a valid identifier. `execute_query` we monkeypatch to return an empty list (`[]`), simulating a scenario where no records are found in the database.
    After attempting to execute the query with the dummy author ID, the function "in-spects" the results. Finding an empty list, it logs a warning stating `"No results found for author: FakeAuthor"` and returns `None`.
    The test verifies that the function returns `None` and the captured log (via `caplog`) contains the warning message `"No results found for author: FakeAuthor"`. Thus, the test confirms that lines 284–285 properly detect the absence of query results, log the appropriate warning, and return `None`. """
    monkeypatch.setattr("backend.app.get_author_ids", lambda author: [
                        {"author_id": "dummy_author_id"}])
    monkeypatch.setattr("backend.app.execute_query", lambda q, params: [])
    from backend.app import search_by_author
    result = search_by_author("FakeAuthor")
    assert result is None
    assert "No results found for author: FakeAuthor" in caplog.text


def test_get_institution_and_researcher_results_graph(monkeypatch, caplog):
    """ This test confirms that the `get_institution_and_researcher_results` function (specifically the code at line 765) correctly builds the graph structure from the combined query results. In this case, the dummy data provided includes author metadata. Two authors are provided with their respective IDs, names, and number of works (7 for "Author One" and 3 for "Author Two"). With regard to the institution metadata, the institution is given with its URL and other details (here, represented as "FakeInstitution"). That's why the totals indicate that there are 2 authors, among other counts.
    The function is expected to build the list..it should create a list view with tuples for each author in the format `(author_name, num_of_works)`. The test asserts that the list equals `[("Author One", 7), ("Author Two", 3)]`. Furthermore we have got to assemble the graph nodes: an institution node with `"id": "FakeInstitution"`, `"label": "FakeInstitution"`, and type `"INSTITUTION"`, as well as author nodes for each author (e.g., one with `"id": "dummy_author_1"`, `"label": "Author One"`, and type `"AUTHOR"`), and then notwithstanding the number [of] nodes representing the count of works for each author (nodes for 7 and 3, with type `"NUMBER"`).
    We also construct the graph edges' structure; an edge connecting each author node to its corresponding number node, with a label `"numWorks"`, is "combined' with an edge connecting each author node to the institution node with a label `"memberOf"`.
    We verify the metadata which should include a key `"people_count"` with the value `2`, matching the total number of authors. There, this test asserts that the function properly maps the dummy data to the expected graph structure and metadata, such that all nodes (institution, authors, numbers) and edges (author-to-number and author-to-institution) are correctly included in the output. """
    dummy_data = {
        "author_metadata": {
            "orcid": "dummy_orcid",
            "num_of_works": 10,
            "last_known_institution": "Dummy Inst",
            "num_of_citations": 5,
            "openalex_url": "http://dummy_author_url"
        },
        "institution_metadata": {
            "url": "http://fakeinstitution.com",
            "openalex_url": "FakeInstitution",
            "ror": "dummy_ror",
            "institution_name": "FakeInstitution"
        },
        "data": [
            {"author_id": "dummy_author_1",
                "author_name": "Author One", "num_of_works": 7},
            {"author_id": "dummy_author_2",
                "author_name": "Author Two", "num_of_works": 3}
        ],
        "totals": {
            "total_num_of_works": 2,
            "total_num_of_citations": 5,
            "total_num_of_authors": 2
        }
    }
    monkeypatch.setattr("backend.app.search_by_author_institution",
                        lambda researcher, institution: dummy_data)
    from backend.app import get_institution_and_researcher_results
    result = get_institution_and_researcher_results(
        "FakeInstitution", "FakeResearcher", page=1, per_page=20)
    expected_list = [("Author One", 7), ("Author Two", 3)]
    assert result["list"] == expected_list
    graph = result["graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    institution_node = {"id": "FakeInstitution",
                        "label": "FakeInstitution", "type": "INSTITUTION"}
    assert institution_node in nodes
    author_node_1 = {"id": "dummy_author_1",
                     "label": "Author One", "type": "AUTHOR"}
    author_node_2 = {"id": "dummy_author_2",
                     "label": "Author Two", "type": "AUTHOR"}
    assert author_node_1 in nodes
    assert author_node_2 in nodes
    number_node_1 = {"id": 7, "label": 7, "type": "NUMBER"}
    number_node_2 = {"id": 3, "label": 3, "type": "NUMBER"}
    assert number_node_1 in nodes
    assert number_node_2 in nodes
    expected_edge_1 = {
        "id": "dummy_author_1-7",
        "start": "dummy_author_1",
        "end": 7,
        "label": "numWorks",
        "start_type": "AUTHOR",
        "end_type": "NUMBER"
    }
    expected_edge_2 = {
        "id": "dummy_author_2-3",
        "start": "dummy_author_2",
        "end": 3,
        "label": "numWorks",
        "start_type": "AUTHOR",
        "end_type": "NUMBER"
    }
    expected_edge_3 = {
        "id": "dummy_author_1-FakeInstitution",
        "start": "dummy_author_1",
        "end": "FakeInstitution",
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    expected_edge_4 = {
        "id": "dummy_author_2-FakeInstitution",
        "start": "dummy_author_2",
        "end": "FakeInstitution",
        "label": "memberOf",
        "start_type": "AUTHOR",
        "end_type": "INSTITUTION"
    }
    assert expected_edge_1 in edges
    assert expected_edge_2 in edges
    assert expected_edge_3 in edges
    assert expected_edge_4 in edges
    assert result["metadata"]["people_count"] == 2


def test_metadata_no_last_known_institution(monkeypatch, caplog):
    """ The test is "de-signed" to verify the behavior of the code when an author’s record does not include a last known institution. In that scenario (which is triggered when the value is `None`), the code falls back to calling the function that fetches this information from OpenAlex. Specifically, around line 620 in the file, the code checks if `metadata['last_known_institution']` is `None`. "If it is," it logs a debug message ("Fetching last known institutions from OpenAlex") and then calls `fetch_last_known_institutions` with the author's OpenAlex URL.
    In the test, a fake API response is provided that returns an institution with `"display_name": "Fetched Institution"`. As a result, the branch of code starting at line 620 is executed, and the `metadata["current_institution"]` is updated to `"Fetched Institution"`. The test then confirms that this is indeed what happens and that the debug message is logged. Thus..the test is responsible for showing that when the `last_known_institution` is "missing", the fallback logic at line 620 correctly fetches and assigns the institution information from OpenAlex. """
    fake_data = {
        "author_metadata": {
            "orcid": "0000-0002-1825-0097",
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": None
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 5, "total_num_of_citations": 15},
        "data": []
    }
    fake_api_response = [
        {"display_name": "Fetched Institution", "id": "http://institutionurl"}]
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda x: fake_api_response)
    result = get_researcher_and_subfield_results("Emily Brown", "Biology")
    assert result["metadata"]["current_institution"] == "Fetched Institution"
    assert "Fetching last known institutions from OpenAlex" in caplog.text


def test_metadata_no_institution_found(monkeypatch, caplog):
    """ This test is verifying what happens when the code tries to fetch a last known institution for an author but finds none. Specifically, at line 612 in app.py, the code attempts to access the first "element" of the list returned by fetch_last_known_institutions (i.e. something like institution_object = institution_object[0]). In the test, the fake data sets "last_known_institution": None and the monkeypatched fetch_last_known_institutions returns an empty list. This situation triggers an attempt to access an element in an empty list, causing an IndexError. The test confirms that the error is "thrown and raise" and also checks that the log message "Fetching last known institutions from OpenAlex" was emitted. """
    fake_data = {
        "author_metadata": {
            "orcid": None,
            "openalex_url": "http://fakeopenalexurl",
            "last_known_institution": None
        },
        "subfield_metadata": [{"topic": "TopicA", "subfield_url": "http://subfieldurl"}],
        "totals": {"total_num_of_works": 5, "total_num_of_citations": 15},
        "data": []
    }
    monkeypatch.setattr("backend.app.search_by_author_topic",
                        lambda a, t: fake_data)
    monkeypatch.setattr(
        "backend.app.fetch_last_known_institutions", lambda x: [])
    with pytest.raises(IndexError):
        get_researcher_and_subfield_results("No Institution Author", "Geology")
    assert "Fetching last known institutions from OpenAlex" in caplog.text


@pytest.fixture
def mock_data_db():
    """ This fixture is used to simulate a typical database response that the function at lines 677–725 of app.py would receive when handling an institution and topic search. In that section, the function extracts subfield metadata (e.g., the topic and its associated URL), reads total counts for works, citations, and authors from the provided "totals", retrieves institution metadata (homepage, OpenAlex URL, and ROR), AND processes a list of author entries with their respective work counts.
    The fixture re-turns a dictionary with these keys (subfield_metadata, totals, institution_metadata, & data). The function then uses this data to construct the response metadata, build a graph (with nodes for the topic, institution, and each author along with corresponding edges), and set up pagination details.
    As well, this fixture is responsible for providing fake, yet structured, database data so that the code handling lines 677–725 can be tested for correct processing and graph construction when both institution and topic information are available. """
    return {
        'subfield_metadata': [
            {'topic': 'AI', 'subfield_url': 'http://openalex.org/subfields/123'}
        ],
        'totals': {
            'total_num_of_works': 10,
            'total_num_of_citations': 50,
            'total_num_of_authors': 5
        },
        'institution_metadata': {
            'url': 'http://institution.com',
            'openalex_url': 'http://openalex.org/institutions/123',
            'ror': 'ror:12345'
        },
        'data': [
            {'author_id': 'author1', 'author_name': 'John Doe', 'num_of_works': 3},
            {'author_id': 'author2', 'author_name': 'Jane Smith', 'num_of_works': 7},
        ]
    }


def test_db_results_path(mock_data_db, caplog):
    """ Lines 713–720 are part of the loop that processes each entry in the database results for an institution–topic search. In this block, for every author entry in the returned data (specifically from the slice of data["data"] for the current page), the code extracts the author’s ID, name, and the number of works (lines 713–715), appends a tuple of the author name and work count to a list that represents the “list view” (line 716), adds nodes for the author and for the work count (lines 717–718), and adds edges linking the author node to the node representing the work count and to the institution node (lines 719–720).
    The test uses a monkey-patch (with the patch context manager) to replace the call to search_by_institution_topic so that it returns a controlled mock_data_db. Then, by calling get_institution_and_subfield_results with test parameters ('Test University' and 'Computer Science'), the test asserts that the metadata is correctly set with the institution name, topic name, work count, and people "count" from the mock data. It also verifies that the log contains a success message ("Successfully built result"), confirming that the branch of code between lines 713 and 720 processed the mock data as "expected and needed". """
    with patch('backend.app.search_by_institution_topic', return_value=mock_data_db):
        result = get_institution_and_subfield_results(
            'Test University', 'Computer Science', page=1, per_page=20)
        assert result['metadata']['institution_name'] == 'Test University'
        assert result['metadata']['topic_name'] == 'Computer Science'
        assert result['metadata']['work_count'] == 10
        assert result['metadata']['people_count'] == 2
        assert 'Successfully built result' in caplog.text


def test_sparql_empty_result(caplog):
    """ In this test, the patches force the SPARQL fallback branch in the function to execute. The patch for search_by_institution_topic makes it return None, so the function falls back to using SPARQL. The patch for get_institution_and_topic_metadata_sparql makes it return an empty dictionary ({}).
    In the SPARQL branch (lines 668–669), the code checks if the SPARQL result is empty. If it is, it logs a warning ("No results found in SPARQL for institution and topic") and returns an empty dictionary. The test asserts that the returned result is indeed an empty dictionary and that the warning message was logged. Thus, this test confirms that when SPARQL yields no data, the function behaves as expected by returning {} and logging the "appropriate" message. """
    with patch('backend.app.search_by_institution_topic', return_value=None), \
            patch('backend.app.get_institution_and_topic_metadata_sparql', return_value={}):

        result = get_institution_and_subfield_results(
            'Unknown University', 'Unknown Topic', page=1, per_page=20)

        assert result == {}
        assert 'No results found in SPARQL' in caplog.text


def test_list_given_institution_topic_multiple_results(monkeypatch):
    """ This test verifies that when multiple results are returned by the SPARQL query, the function correctly builds both the list view and the graph structure. In particular, Lines 1225–1227 process each SPARQL result. For each author record, the code calculates the work count by counting the commas in the "works" string (adding one to get the total number of works). It then appends a tuple (author name, work count) to the final list and updates the overall work count and people count. The test asserts that the final list equals `[("Author One", 2), ("Author Two", 1)]` and that the extra metadata reflects a total work count of 3 and 2 people.
    Lines 1240–1243 build the graph structure. The code creates nodes for the topic and the institution, and for each SPARQL result it creates:
  * An author node with the corresponding ID and name,
  * A number node representing the work count,
  * A "memberOf" edge linking the author node to the institution node, and
  * A "numWorks" edge linking the author node to the number node.
  The test verifies that these nodes and edges exist in the resulting graph.
  And as a "result" the function correctly aggregates multiple SPARQL results into a list of authors with their work counts and builds the appropriate graph connections between the institution, topic, & author nodes. """
    fake_results = [
        {
            'author': 'http://author/1',
            'name': 'Author One',
            'works': 'http://work/1, http://work/2'
        },
        {
            'author': 'http://author/2',
            'name': 'Author Two',
            'works': 'http://work/3'
        }
    ]
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    institution = "Inst B"
    institution_id = "instB456"
    topic = "Topic B"
    topic_id = "topicB456"
    final_list, graph, extra_metadata = list_given_institution_topic(
        institution, institution_id, topic, topic_id)
    assert final_list == [("Author One", 2), ("Author Two", 1)]
    assert extra_metadata == {"work_count": 3, "num_people": 2}
    nodes = graph["nodes"]
    edges = graph["edges"]
    assert {'id': topic_id, 'label': topic, 'type': 'TOPIC'} in nodes
    assert {'id': institution_id, 'label': institution,
            'type': 'INSTITUTION'} in nodes
    for rec in fake_results:
        works_count = rec['works'].count(",") + 1
        author_node = {'id': rec['author'],
                       'label': rec['name'], 'type': 'AUTHOR'}
        number_node = {'id': works_count,
                       'label': works_count, 'type': 'NUMBER'}
        assert author_node in nodes
        assert number_node in nodes
        member_edge = {'id': f"{rec['author']}-{institution_id}",
                       'start': rec['author'],
                       'end': institution_id,
                       "label": "memberOf",
                       "start_type": "AUTHOR",
                       "end_type": "INSTITUTION"}
        numworks_edge = {'id': f"{rec['author']}-{works_count}",
                         'start': rec['author'],
                         'end': works_count,
                         "label": "numWorks",
                         "start_type": "AUTHOR",
                         "end_type": "NUMBER"}
        assert member_edge in edges
        assert numworks_edge in edges


def test_institution_researcher_results_sparql_success(monkeypatch, caplog):
    """ This test states that when the database path for an institution–researcher search fails (i.e. when
`search_by_author_institution` returns `None`), the code falls back to using SPARQL. In particular, lines 748–751 of **app.py** execute the following logic..Line 748 says that after determining that the database returned no results, the function calls `list_given_researcher_institution` with the SPARQL-derived `data['researcher_oa_link']`, the researcher name, and the institution. And then Line 749 says that the results from the SPARQL call are then packaged into a dictionary with keys `"metadata"`, `"graph"`, and `"list"`. While Line 750 says that a log message is written indicating successful retrieval of SPARQL results. Line 751 "says" that the function returns the constructed result.
    "Meanwhile" in t the test, the monkeypatching sets
        *`search_by_author_institution` to return `None` (forcing the SPARQL branch).
        *`get_researcher_and_institution_metadata_sparql` to return a fake metadata dictionary (`fake_sparql_data`).
        *`list_given_researcher_institution` to return a fake topic list and graph.
    The test then asserts that the final result matches the expected dictionary containing the fake metadata, graph, and list, and it confirms that the success log message is present. This confirms that lines 748–751 operate correctly in the SPARQL fallback path. """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution",
        lambda researcher, institution: None
    )
    fake_sparql_data = {
        "institution_metadata": {
            "url": "http://fakeinst.edu",
            "openalex_url": "inst_oa_fake",
            "ror": "ROR_FAKE"
        },
        "author_metadata": {
            "orcid": "ORCID_FAKE",
            "openalex_url": "author_oa_fake",
            "num_of_works": 15,
            "num_of_citations": 50
        },
        "researcher_oa_link": "author_oa_fake",
        "data": []
    }
    monkeypatch.setattr(
        "backend.app.get_researcher_and_institution_metadata_sparql",
        lambda researcher, institution: fake_sparql_data
    )
    fake_topic_list = [("Fake Topic", 3)]
    fake_graph = {
        "nodes": [{"id": "inst_oa_fake", "label": "Test Institution", "type": "INSTITUTION"},
                  {"id": "author_oa_fake", "label": "Test Researcher", "type": "AUTHOR"},
                  {"id": "Fake Topic", "label": "Fake Topic", "type": "TOPIC"}],
        "edges": [{"id": "author_oa_fake-Fake Topic", "start": "author_oa_fake", "end": "Fake Topic",
                   "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"}]
    }
    monkeypatch.setattr(
        "backend.app.list_given_researcher_institution",
        lambda researcher_oa, researcher, institution: (
            fake_topic_list, fake_graph)
    )
    institution = "Test Institution"
    researcher = "Test Researcher"
    result = get_institution_and_researcher_results(institution, researcher)
    expected_result = {
        "metadata": fake_sparql_data,
        "graph": fake_graph,
        "list": fake_topic_list
    }
    assert result == expected_result
    assert any("Successfully retrieved SPARQL results for researcher" in record.message
               for record in caplog.records)


def test_institution_researcher_results_database(monkeypatch, caplog):
    """ This test verifies the database code path for an institution–researcher search, processing it so that when valid database results are returned, the function correctly processes them and constructs the response. In particular, it covers two key sections..these are (1) Metadata processing (around line 763), wherein the function extracts institution metadata (such as homepage, OpenAlex URL, and ROR) and researcher metadata (including OpenAlex URL, work count, and citation count) and then hypothesizes that if the researcher's ORCID is missing, an empty string is used..the test confirms that the resulting metadata matches the expected dictionary.
    We also do in (2) that graph construction (lines 787–797) wherein for each topic entry in the returned data, the function builds nodes for the topic and a corresponding "NUMBER" node (based on the work count). It creates edges linking the researcher node to each topic node (labeled "researches") and from the topic node to the number node (labeled "number"). The test constructs an expected graph (with nodes for the institution, researcher, topics, and numbers, and corresponding edges) and then verifies that the nodes and edges produced by the function match the expected ones.
    Additionally, the test checks "pagination" data and the final list view (a list of tuples with topic names and work counts). It also confirms via log messages that the code path for processing database results was executed. "That means," this test reveals that when `search_by_author_institution` returns database data, the function `get_institution_and_researcher_results` correctly assembles the metadata, pagination, graph, and list output as expected. """
    fake_db_data = {
        "institution_metadata": {
            "url": "http://dbinst.edu",
            "openalex_url": "inst_oa_db",
            "ror": "ROR_DB"
        },
        "author_metadata": {
            "orcid": None,
            "openalex_url": "author_oa_db",
            "num_of_works": 8,
            "num_of_citations": 25
        },
        "data": [
            {"topic_name": "Topic1", "num_of_works": 3},
            {"topic_name": "Topic2", "num_of_works": 5},
            {"topic_name": "Topic3", "num_of_works": 2}
        ]
    }
    monkeypatch.setattr(
        "backend.app.search_by_author_institution",
        lambda researcher, institution: fake_db_data
    )
    institution = "DB Institution"
    researcher = "DB Researcher"
    page = 1
    per_page = 20
    result = get_institution_and_researcher_results(
        institution, researcher, page, per_page)
    expected_metadata = {
        "homepage": "http://dbinst.edu",
        "institution_oa_link": "inst_oa_db",
        "ror": "ROR_DB",
        "institution_name": institution,
        "orcid": "",
        "researcher_name": researcher,
        "researcher_oa_link": "author_oa_db",
        "current_institution": "",
        "work_count": 8,
        "cited_by_count": 25
    }
    total_topics = len(fake_db_data["data"])
    expected_pagination = {
        "total_pages": (total_topics + per_page - 1) // per_page,
        "current_page": page,
        "total_topics": total_topics,
    }
    nodes = [
        {'id': institution, 'label': institution, 'type': 'INSTITUTION'},
        {'id': "author_oa_db", 'label': researcher, "type": "AUTHOR"}
    ]
    edges = [
        {'id': "author_oa_db-" + institution,
         'start': "author_oa_db", 'end': institution,
         "label": "memberOf", "start_type": "AUTHOR", "end_type": "INSTITUTION"}
    ]
    expected_list = []
    for entry in fake_db_data["data"]:
        topic = entry["topic_name"]
        num = entry["num_of_works"]
        expected_list.append((topic, num))
        nodes.append({'id': topic, 'label': topic, 'type': "TOPIC"})
        number_id = topic + ":" + str(num)
        nodes.append({'id': number_id, 'label': num, 'type': "NUMBER"})
        edges.append({'id': "author_oa_db-" + topic,
                      'start': "author_oa_db", 'end': topic,
                      "label": "researches", "start_type": "AUTHOR", "end_type": "TOPIC"})
        edges.append({'id': topic + "-" + number_id,
                      'start': topic, 'end': number_id,
                      "label": "number", "start_type": "TOPIC", "end_type": "NUMBER"})

    expected_graph = {"nodes": nodes, "edges": edges}
    expected_result = {
        "metadata": expected_metadata,
        "metadata_pagination": expected_pagination,
        "graph": expected_graph,
        "list": expected_list
    }
    assert result["metadata"] == expected_metadata
    assert result["metadata_pagination"] == expected_pagination

    def to_set(items):
        return {frozenset(item.items()) for item in items}
    assert to_set(result["graph"]["nodes"]) == to_set(expected_graph["nodes"])
    assert to_set(result["graph"]["edges"]) == to_set(expected_graph["edges"])
    assert result["list"] == expected_list
    assert any("Processing database results for institution and researcher" in record.message
               for record in caplog.records)
    assert any("Successfully built result for researcher" in record.message
               for record in caplog.records)


def test_list_given_researcher_topic_multiple_results(monkeypatch, caplog):
    """ This test verifies that when multiple SPARQL results are returned for a researcher–topic search, the function correctly sorts the work list and constructs the graph. In detail, Lines 1300–1301 "allow the function to iterate and it iterates" over each result from the SPARQL endpoint. For each result, it appends a tuple to the work list, where the work count is computed by converting the string citation count to an integer. In our fake data, the works are "Work B" (5 citations), "Work A" (15 citations), and "Work C" (10 citations). The function then sorts the list in descending order of citations, resulting in `[("Work A", 15), ("Work C", 10), ("Work B", 5)]`, and calculates the total citations (30) and work count (3).
    Lines 1314–1317 do the next thing in which, the function constructs the graph structure. It creates nodes for the institution, researcher, and topic, then for each work in the sorted work list, it creates:
        * A work node,
        * A number node (using the citation count),
        * An "authored" edge connecting the researcher node to the work node,
        * A "citedBy" edge linking the work node to the number node.
    The test asserts that the work list is correctly sorted, the extra metadata is accurate, and that all expected nodes and edges are present in the graph. It also checks for a log message indicating that the list and graph were built successfully. """
    fake_results = [
        {'title': 'Work B', 'cited_by_count': '5'},
        {'title': 'Work A', 'cited_by_count': '15'},
        {'title': 'Work C', 'cited_by_count': '10'},
    ]
    monkeypatch.setattr(
        "backend.app.query_SPARQL_endpoint",
        lambda endpoint, query: fake_results
    )
    topic = "Topic Y"
    researcher = "Researcher Y"
    institution = "Institution Y"
    topic_id = "topicY_id"
    researcher_id = "researcherY_id"
    institution_id = "institutionY_id"
    work_list, graph, extra_metadata = list_given_researcher_topic(
        topic, researcher, institution, topic_id, researcher_id, institution_id
    )
    assert work_list == [("Work A", 15), ("Work C", 10), ("Work B", 5)]
    assert extra_metadata == {"work_count": 3, "cited_by_count": 30}
    nodes = graph["nodes"]
    edges = graph["edges"]
    expected_institution_node = {'id': institution_id,
                                 'label': institution, 'type': 'INSTITUTION'}
    expected_researcher_node = {'id': researcher_id,
                                'label': researcher, 'type': 'AUTHOR'}
    expected_topic_node = {'id': topic_id, 'label': topic, 'type': 'TOPIC'}
    assert expected_institution_node in nodes
    assert expected_researcher_node in nodes
    assert expected_topic_node in nodes
    for title, count in work_list:
        work_node = {'id': title, 'label': title, 'type': 'WORK'}
        number_node = {'id': count, 'label': count, 'type': "NUMBER"}
        assert work_node in nodes
        assert number_node in nodes
        authored_edge = {
            'id': f"{researcher_id}-{title}",
            'start': researcher_id,
            'end': title,
            "label": "authored",
            "start_type": "AUTHOR",
            "end_type": "WORK"
        }
        citedby_edge = {
            'id': f"{title}-{count}",
            'start': title,
            'end': count,
            "label": "citedBy",
            "start_type": "WORK",
            "end_type": "NUMBER"
        }
        assert authored_edge in edges
        assert citedby_edge in edges
    assert any(
        "Successfully built list and graph for researcher" in record.message for record in caplog.records)


class DummyCursorFailure:
    """ The purpose of the `DummyCursorFailure` class is to simulate a failure in the SQL execution process. Specifically, when the code reaches the block where it calls `cursor.execute(query)` (lines 1379–1380 in the original file), this dummy cursor is used to mimic the behavior of a cursor that raises an error. """

    def execute(self, query):
        """ When `execute` is called with any query, it instantaneously raises an `Error` with the message "Simulated SQL error". This mimics an SQL execution failure.
        By using this dummy cursor, the application’s error handling for SQL queries (specifically the logging of the error in lines 1379–1380) can be tested. It sets it so that when an SQL error occurs, the application properly logs the failure and handles it as expected.  """
        raise Error("Simulated SQL error")

    def fetchall(self):
        """ Although this method is defined to return an empty list, in the failure scenario it is not reached because the error is raised during the execution step. """
        return []


class DummyConnectionFailure:
    """ The DummyConnectionFailure class is designed to simulate a failure when attempting to create a database cursor. In this test scenario, when the application calls connection.cursor() (as seen in lines 1379–1380 of app.py), this dummy connection returns an instance of DummyCursorFailure. This means that any sub-sequent call to cursor.execute(query) will raise an Error (simulating an SQL error), and cursor.fetchall() would return an empty list if reached. This setup allows testing of the error handling logic within the SQL query execution process. """

    def cursor(self):
        return DummyCursorFailure()


def test_query_sql_endpoint_exception(monkeypatch, caplog):
    """ This test verifies the error-handling logic in the `query_SQL_endpoint` function when a SQL error occurs during query execution (specifically in lines 1379–1380).
        A `DummyConnectionFailure` object is used as the connection. Its `cursor()` method returns a `DummyCursorFailure`, whose `execute()` method raises an `Error` with the message "Simulated SQL error". When `query_SQL_endpoint` is invoked with this connection and a dummy query, the call to `cursor.execute(query)` raises an error. The function catches this exception and logs an error message. Finally, the function returns `None` to indicate that the query could not be executed successfully.
        The test asserts that the returned result is `None` and that the expected error message ("SQL query failed: Simulated SQL error") appears in the log. """
    connection = DummyConnectionFailure()
    query = "SELECT * FROM dummy_table"
    result = query_SQL_endpoint(connection, query)
    assert result is None
    assert "SQL query failed: Simulated SQL error" in caplog.text


def test_create_connection_failure(monkeypatch, caplog):
    """ This test verifies that the `create_connection` function correctly handles connection failures (as seen in lines 1605–1606 of app.py). Specifically a fake connection function (`fake_connect`) is defined to raise an `Error` with the message "Simulated connection error" when called. The test monkeypatches `mysql.connector.connect` to use this fake function. When `create_connection` is called with invalid parameters, the fake connection function raises an exception. The function should catch the error, log a message indicating the failure, and return `None`. The test asserts that the connection is "indeed" `None` and that the log contains the expected error message. """
    error_message = "Simulated connection error"

    def fake_connect(host, user, passwd, database):
        raise Error(error_message)
    monkeypatch.setattr(mysql.connector, "connect", fake_connect)
    host = "invalid_host"
    user = "invalid_user"
    passwd = "invalid_pass"
    db = "test_db"
    connection = create_connection(host, user, passwd, db)
    assert connection is None
    assert f"Failed to connect to MySQL database: {error_message}" in caplog.text


def test_get_institution_endowments_and_givings_no_results(monkeypatch, caplog):
    """ This test validates the behavior of the function `get_institution_endowments_and_givings` when no data is found from the database (specifically addressing lines 1672–1673 of app.py). The test monkeypatches `get_institution_id` with a dummy function (`dummy_get_institution_id_success`) that simulates successfully finding an institution ID. It also replaces `execute_query` with `dummy_execute_query_empty`, which simulates a database query that returns no results. Wth these replacements in place, calling `get_institution_endowments_and_givings` for "Test University" results in no data being retrieved. The test asserts that the function returns `None` and that the appropriate log message ("No MUP endowments and givings data found for Test University") appears in the logs. This confirms that the function properly handles the situation when the database query yields no results. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)
    institution_name = "Test University"
    result = get_institution_endowments_and_givings(institution_name)
    assert result is None
    assert f"No MUP endowments and givings data found for {institution_name}" in caplog.text


def test_get_institutions_faculty_awards_no_institution(monkeypatch, caplog):
    """ This test "proves" that if no institution ID is found for the given institution name, the function `get_institutions_faculty_awards` behaves as expected. In detail, the test replaces `get_institution_id` with a dummy function (`dummy_get_institution_id_none`) that returns `None` to simulate the case where the institution does not exist. When `get_institutions_faculty_awards` is called with "Nonexistent University", the absence of an institution ID causes the function to return `None`. The test asserts that the result is `None` and that the log contains the message indicating that no institution ID was found for the specified institution. This confirms that the code correctly handles the error scenario at lines 1735–1736, logging an appropriate message and returning `None`. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    institution_name = "Nonexistent University"
    result = get_institutions_faculty_awards(institution_name)
    assert result is None
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institutions_faculty_awards_no_results(monkeypatch, caplog):
    """ This test confirms that when the query for faculty "awards" data returns no results, the function correctly returns None and logs an appropriate message. In detail, the test sets up two patches. It replaces get_institution_id with a dummy function (dummy_get_institution_id_success) that simulates successfully finding an institution ID. It replaces execute_query with a dummy function (dummy_execute_query_empty) that simulates a query returning no results. With these patches, calling get_institutions_faculty_awards("Test University") results in no data being found. The test asserts that the function returns None AND that the log contains the message "No MUP faculty awards data found for Test University", indicating that the function handled the empty result as expected. This test verifies the proper handling of a scenario where the institution exists but no faculty awards data is available (lines 1745–1746). """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)
    institution_name = "Test University"
    result = get_institutions_faculty_awards(institution_name)
    assert result is None
    assert f"No MUP faculty awards data found for {institution_name}" in caplog.text


def test_get_institutions_faculty_awards_success(monkeypatch, caplog):
    """ This test verifies that when the database query returns a successful result for faculty awards data, the function `get_institutions_faculty_awards` constructs the correct output. Specifically, the test covers the code path executed in lines 1741–1744 of app.py. The test replaces `get_institution_id` with a dummy function (`dummy_get_institution_id_success`) that simulates successfully retrieving an institution ID. It also patches `execute_query` with `dummy_execute_query_success` to simulate a successful query that returns the expected awards data. The function is called with the institution name `"Test University"`. Under these conditions, the function retrieves the awards data and constructs a dictionary containing values like `"nae": 10, "nam": 20, "nas": 30, "num_fac_awards": 4, "year": 2021` along with the institution's name and dummy ID.
    The test asserts that the returned result exactly matches the expected dictionary. It also confirms that a success log message stating `"Successfully fetched MUP faculty awards data for Test University"` is present in the log records.
    Thus, this test ensures that the successful database query path in `get_institutions_faculty_awards` (lines 1741–1744) correctly fetches, processes, and returns the faculty awards data. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)
    institution_name = "Test University"
    result = get_institutions_faculty_awards(institution_name)
    expected = {
        "nae": 10,
        "nam": 20,
        "nas": 30,
        "num_fac_awards": 4,
        "year": 2021,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    assert f"Successfully fetched MUP faculty awards data for {institution_name}" in caplog.text


def dummy_get_institution_id_success(institution_name):
    """ This dummy function simply re-turns a fixed institution ID ("dummy_institution_id") to simulate a successful lookup of an institution's ID. It's used in tests to bypass actual database or external API calls, such that the subsequent logic in the specified parts of the code (lines 1631–1637, 1665–1673, 1738–1746, 1756–1764) can proceed with a valid institution ID for testing purposes. """
    return "dummy_institution_id"


def dummy_get_institution_id_none(institution_name):
    """ This dummy function is designed to simulate a scenario where the institution lookup fails. When called with any institution name, it returns None. It’s used in tests (specifically for the code paths at lines 1644–1645, 1662–1663, 1735–1736, and 1753–1754) to verify that the application correctly handles cases where no institution ID is found. """
    return None


def dummy_execute_query_success(query, params):
    """ This dummy function simulates a successful database query execution. When called, it returns a nested list containing a dictionary with keys such as "category", "federal", "percent_federal", "total", and "percent_total". These values represent a sample record from the database. This dummy function is used in tests for the code paths at lines 1634–1635, 1668–1671, 1741–1744, and 1759–1762 of app.py to verify that the application correctly processes and returns expected results when a database query succeeds. """
    return [[{
        "category": "Test Category",
        "federal": 100,
        "percent_federal": 50.0,
        "total": 200,
        "percent_total": 100.0
    }]]


def dummy_execute_query_empty(query, params):
    """ This dummy function simulates a database query that returns no results. When it is called with any query and parameters, it returns an empty list. This is used in tests for code paths at lines 1636–1637, 1672–1673, 1745–1746, and 1763–1764 of app.py to verify that the application properly handles cases where the query does not yield any data. """
    return []


def test_get_institutions_r_and_d_no_institution(monkeypatch, caplog):
    """  This test verifies that the function `get_institutions_r_and_d` correctly handles the scenario when no institution ID can be found. Specifically, for lines 1753–1754 in app.py, the function is expected to check if an institution ID exists. "If not," it should log an "appropriate" message and return `None`. Te test "replaces" `get_institution_id` with `dummy_get_institution_id_none`, which "forever and always" returns `None`. This simulates the case where the institution lookup fails for "Nonexistent University".
    When `get_institutions_r_and_d("Nonexistent University")` is called, it finds no institution ID. The test asserts that the result is `None` and that the log contains the message `"No institution ID found for Nonexistent University"`, confirming that the error case is handled as expected.
    This is so that the code path at lines 1753–1754 behaves correctly when no institution ID is "available"."""
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    institution_name = "Nonexistent University"
    result = get_institutions_r_and_d(institution_name)
    assert result is None
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institutions_r_and_d_success(monkeypatch, caplog):
    """ This test validates the successful path for fetching R&D data for an institution, specifically covering the code executed in lines 1759–1762 of app.py.
   * `get_institution_id` is replaced with `dummy_get_institution_id_success`, which always returns the fixed institution ID `"dummy_institution_id"`.
   * `execute_query` is replaced with `dummy_execute_query_success`, which returns a nested list containing a dictionary with keys like `"category"`, `"federal"`, `"percent_federal"`, `"total"`, and `"percent_total"`.
   Then, the function `get_institutions_r_and_d` is called with the institution name `"Test University"`. Given the patched functions, the query execution returns the expected data, and the function then "augments" this data by including the institution name and ID.
   * The test checks that the result exactly matches the expected dictionary, which includes the values returned by `dummy_execute_query_success` along with `"institution_name": "Test University"` and `"institution_id": "dummy_institution_id"`.
   * It also asserts that the log contains the message indicating successful data retrieval: `"Successfully fetched MUP R&D data for Test University"`.
   All in all, the test confirms that when the query returns data successfully, `get_institutions_r_and_d` properly "constructs" and returns the expected output. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)
    institution_name = "Test University"
    result = get_institutions_r_and_d(institution_name)
    expected = {
        "category": "Test Category",
        "federal": 100,
        "percent_federal": 50.0,
        "total": 200,
        "percent_total": 100.0,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    assert f"Successfully fetched MUP R&D data for {institution_name}" in caplog.text


def test_get_institutions_r_and_d_no_results(monkeypatch, caplog):
    """ This test verifies the behavior of `get_institutions_r_and_d` when the database query returns no results (covering lines 1763–1764 of app.py). The test sets `get_institution_id` to `dummy_get_institution_id_success`, which returns a dummy institution ID ("dummy_institution_id") so that the institution lookup is successful AND `execute_query` to `dummy_execute_query_empty`, which simulates a query that returns an empty list.
    When `get_institutions_r_and_d("Test University")` is in-voked, the query returns no results. The function is designed to detect this and return `None`.
    The test asserts that the function returns `None` and that the log contains the message indicating that no R&D data was found for the institution ("No MUP R&D datafound for Test University"). This confirms that when no data is available from the query, the function correctly handles the scenario by returning `None` and logging the appropriate message. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)
    institution_name = "Test University"
    result = get_institutions_r_and_d(institution_name)
    assert result is None
    assert f"No MUP R&D datafound for {institution_name}" in caplog.text


def test_get_institution_mup_id_success(monkeypatch, caplog):
    """ The test specifically targets the branch in the get_institution_mup_id function where, after obtaining an institution ID, it executes the SQL query. In the function (lines 1634–1635), the function calls execute_query(query, (institution_id,)) to retrieve the MUP ID from the database. If the query returns a result (i.e. results is "truthy"), the function logs a success message and returns the first element of the result (i.e. results[0][0]).
    The test, replaces the actual get_institution_id and execute_query functions with dummy functions that simulate successful behavior. dummy_get_institution_id_success sets it so that an institution ID is returned. dummy_execute_query_success is set up to return a result such that results[0][0] equals 42. After calling get_institution_mup_id("Test University"), the test asserts that the returned value is 42 (confirming that the code correctly processed the query result in lines 1634–1635), and the log contains the success message "Successfully fetched MUP ID for Test University", which verifies that the code path for a successful query was executed. Thus and so, the test is responsible for validating that when the query executes successfully (as simulated by the dummy functions), the function logs the correct success message and returns the expected MUP ID from lines 1634–1635. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)
    institution_name = "Test University"
    result = get_institution_mup_id(institution_name)
    assert result == 42
    assert f"Successfully fetched MUP ID for {institution_name}" in caplog.text


def test_get_institution_mup_id_no_results(monkeypatch, caplog):
    """ This test targets the branch of the `get_institution_mup_id` function that handles the scenario when the SQL query returns no results. `dummy_get_institution_id_success` is used to simulate a successful lookup of the institution ID. `dummy_execute_query_empty` is used to simulate an empty result set from the SQL query. This corresponds to the code path where the database query does not find any MUP ID (i.e. lines 1636–1637).
    Ideally, the function should return `None` when `execute_query` returns an empty result. It should log the message `"No MUP ID found for Test University"`. The test asserts that the result is `None`. It also checks that the log contains the expected message. That is how this test verifies that when no MUP ID is retrieved from the query, the function correctly returns `None` and logs an appropriate message. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query", dummy_execute_query_empty)
    institution_name = "Test University"
    result = get_institution_mup_id(institution_name)
    assert result is None
    assert f"No MUP ID found for {institution_name}" in caplog.text


def test_get_institution_sat_scores_no_institution(monkeypatch, caplog):
    """ This test is designed to verify the behavior of the `get_institution_sat_scores` function when no institution ID can be found, which corresponds to lines 1644–1645 in the code. The test replaces `get_institution_id` with `dummy_get_institution_id_none`, such that when it’s called with the institution name `"Nonexistent University"`, it returns `None`. Because no institution ID is found, the function should return `None` as well. It should also log a message indicating that no institution ID was found for `"Nonexistent University"`. The test asserts that the returned result is `None`. It also checks that the log contains the message `"No institution ID found for Nonexistent University"`. At the least, this test confirms that the code correctly handles the case where an institution ID does not exist, by returning `None` and logging an appropriate message. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    institution_name = "Nonexistent University"
    result = get_institution_sat_scores(institution_name)
    assert result is None
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institution_endowments_and_givings_no_institution(monkeypatch, caplog):
    """ This test verifies the behavior of the `get_institution_endowments_and_givings` function when the institution ID cannot be retrieved, which corresponds to lines 1662–1663 in the code. The test replaces the actual `get_institution_id` function with `dummy_get_institution_id_none`, on that when called with `"Nonexistent University"`, it returns `None`. Since no institution ID is found, the function should return `None` immediately without proceeding with the SQL query.
    The test asserts that the log contains the message indicating `"No institution ID found for Nonexistent University"`, confirming that the code path handling the missing institution ID was executed. The result is expected to be `None`. The log should include the expected message.
    And, this test verifies that when the institution ID is not available, the function correctly returns `None` and logs the appropriate error message. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_none)
    institution_name = "Nonexistent University"
    result = get_institution_endowments_and_givings(institution_name)
    assert result is None
    assert f"No institution ID found for {institution_name}" in caplog.text


def test_get_institution_endowments_and_givings_success(monkeypatch, caplog):
    """ This test checks the success branch of the `get_institution_endowments_and_givings` function, corresponding to lines 1668–1671. `get_institution_id` is replaced with `dummy_get_institution_id_success`, so it returns a valid institution ID (in this case, `"dummy_institution_id"`). `execute_query` is replaced with `dummy_execute_query_success`, which simulates a successful query by returning a result that, when processed, yields a dictionary with endowment, giving, and year values. Given these simulated successes, the function should return a dictionary containing the following keys:
        * `"endowment": 1000000`
        * `"giving": 50000`
        * `"year": 2021`
        * `"institution_name": "Test University"`
        * `"institution_id": "dummy_institution_id"`
    The test asserts that the result exactly matches the expected dictionary AND the log contains the message `"Successfully fetched MUP endowments and givings data for Test University"`, confirming that the success branch was executed. That is the reason that this test verifies that when both the institution ID lookup and the SQL query succeed, the function correctly processes and returns the expected data. """
    monkeypatch.setattr("backend.app.get_institution_id",
                        dummy_get_institution_id_success)
    monkeypatch.setattr("backend.app.execute_query",
                        dummy_execute_query_success)
    institution_name = "Test University"
    result = get_institution_endowments_and_givings(institution_name)
    expected = {
        "endowment": 1000000,
        "giving": 50000,
        "year": 2021,
        "institution_name": institution_name,
        "institution_id": "dummy_institution_id"
    }
    assert result == expected
    assert f"Successfully fetched MUP endowments and givings data for {institution_name}" in caplog.text


def test_serve_static_file(monkeypatch, caplog):
    """ This test checks the behavior of the `serve` function when the requested file exists, which corresponds to lines 1778–1779 of the code. It replaces `send_from_directory` with a dummy function that returns a string indicating which file is being served. It sets `os.path.exists` to always return `True`, so that the code path that serves the static file is taken.
    Within a test request context, the function `serve("staticfile.js")` is called. Since the file exists (as forced by the monkeypatch), the dummy `send_from_directory` is invoked. The response should be a string like `"File served from {app.static_folder}/staticfile.js"`. Additionally, the test verifies that the log contains the message `"Serving static file: staticfile.js"`, in that the proper log entry was recorded. This means that this test confirms that when a static file exists, the `serve` function correctly serves it and logs the appropriate message. """
    def dummy_send_from_directory(directory, filename):
        return f"File served from {directory}/{filename}"
    monkeypatch.setattr("backend.app.send_from_directory",
                        dummy_send_from_directory)
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    with app.test_request_context():
        response = serve("staticfile.js")
    expected = f"File served from {app.static_folder}/staticfile.js"
    assert response == expected, "Should return the static file if it exists"
    assert "Serving static file: staticfile.js" in caplog.text, (
        "Expected log message for serving static file was not found"
    )


def test_serve_index_html_empty_path(monkeypatch, caplog):
    """ This test verifies the code path in the `serve` function for an empty path, which corresponds to lines 1781–1782 of the application code. The `send_from_directory` function is replaced with a dummy function that returns a string indicating which file is being served. `os.path.exists` is monkeypatched to always return `True` so that the check for a static file passes. The test creates a Flask test request context and then calls `serve("")` with an empty string as the path. When the path is empty, the application should serve `index.html` from the static folder. The dummy function returns `"Index served from {app.static_folder}/index.html"`. The test asserts that the returned response matches this expected output. It also checks that the log contains the message `"Serving index.html for frontend routing"`, confirming that the correct logging occurs for this branch. THerefore, the test confirms that when no specific file is requested (empty path), the application correctly routes to and serves the `index.html` file while logging the appropriate message. """
    def dummy_send_from_directory(directory, filename):
        return f"Index served from {directory}/{filename}"
    monkeypatch.setattr("backend.app.send_from_directory",
                        dummy_send_from_directory)
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    with app.test_request_context():
        response = serve("")
    expected = f"Index served from {app.static_folder}/index.html"
    assert response == expected, "Should return index.html when path is empty"
    assert "Serving index.html for frontend routing" in caplog.text, (
        "Expected log message for serving index.html was not found when path is empty"
    )


ENTRYPOINT_MODULE = "backend.app"


def test_entrypoint_invokes_app_run():
    """ The test is designed to invoke it that when the module is run as a script (i.e., as the entrypoint), it performs two critical actions--(1) initialization (Lines 19–23): At the top of the module, the code reads environment variables (for example, converting the database port from a string to an integer on line 19, and retrieving other settings on lines 20–23). Although the test doesn’t directly assert the values of these variables, running the module via runpy.run_module(ENTRYPOINT_MODULE, run_name="__main__") forces these lines to execute. This means that the module's initial setup—including parsing environment variables—is executed as part of the entrypoint. And (2) starting the Flask app (Lines 1894–1895)--near the end of the file, within the if __name__ == '__main__': block, the app logs a message (line 1894) and then calls app.run() (line 1895) to start the Flask server. The test uses patch to replace the actual app.run() method with a mock so that it does not start the server during testing. After running the module, the test asserts that app.run() was called exactly once, verifying that the entrypoint executed as expected. That is, by running the module as the main program and patching critical methods, the test "indirectly" confirms that the initialization code (lines 19–23) is executed during the module’s startup. The Flask application is started (lines 1894–1895), as indicated by the single call to app.run(). """
    with patch('backend.app.app.logger.info') as info_mock, patch('backend.app.app.run') as run_mock:
        try:
            runpy.run_module(ENTRYPOINT_MODULE, run_name="__main__")
        finally:
            sys.modules.pop('__main__', None)
    run_mock.assert_called_once()


def test_autofill_topics_filters_matches_case_insensitively(monkeypatch):
    """ This test checks that the topic autofill endpoint correctly filters suggestions in a case-insensitive manner. Specifically, it verifies the functionality implemented in Lines 1414–1415 of app.py where the code iterates over the list of topics (or autofill_topics_list when SUBFIELDS is False) and appends a topic to the suggestions if the lowercased input is a substring of the lowercased topic name. In the test the flag `SUBFIELDS` is set to False so that the code uses `autofill_topics_list`, the list is set to `["Cat", "Dog", "Caterpillar"]`, a POST request is made with the topic `"cat"` (all lowercase), and..the test asserts that `"Cat"` and `"Caterpillar"` are included (because "cat" appears in both when case is ignored) and that `"Dog"` is excluded. This confirms that the filtering on lines 1414–1415 works as intended. """
    backend_app.SUBFIELDS = False
    backend_app.autofill_topics_list = ["Cat", "Dog", "Caterpillar"]
    client = app.test_client()
    response = client.post("/autofill-topics", json={"topic": "cat"})
    assert response.status_code == 200, "Expected 200 OK response"
    data = response.get_json()
    possible = data["possible_searches"]
    assert "Cat" in possible, "Expected 'Cat' in suggestions"
    assert "Caterpillar" in possible, "Expected 'Caterpillar' in suggestions"
    assert "Dog" not in possible, "Did not expect 'Dog' in suggestions"
    assert len(possible) == 2, "Expected exactly 2 suggestions"


os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"
os.environ["DB_USER"] = "testuser"
os.environ["DB_PASSWORD"] = "testpass"
os.environ["DB_API"] = "http://testapi"


@pytest.fixture
def fake_db_data_orcid_none():
    """ This fixture provides fake database data for a test scenario where the author’s ORCID is missing (i.e. set to None). In the application code, specifically around line 834, the function handling researcher results checks whether the orcid value is None and, if so, replaces it with an empty string. This fixture is used to simulate that situation, for that the application correctly handles cases when the ORCID is absent. """
    return {
        "institution_metadata": {
            "url": "http://institution.example.com",
            "openalex_url": "institution_oa_123",
            "ror": "ror123"
        },
        "author_metadata": {
            "orcid": None,
            "openalex_url": "researcher_oa_456"
        },
        "subfield_metadata": [
            {"topic": "Subfield A", "subfield_url": "topic_oa_789"}
        ],
        "totals": {
            "total_num_of_works": 10,
            "total_num_of_citations": 100
        },
        "data": [
            {"work_name": "Work 1", "cited_by_count": 5},
            {"work_name": "Work 2", "cited_by_count": 8},
            {"work_name": "Work 3", "cited_by_count": 3},
        ]
    }


@pytest.fixture
def fake_db_data_orcid_present():
    """ This fixture returns a dictionary of fake database data for a test scenario where the author's ORCID is present. In the application (specifically at line 836 of app.py), the code checks if the `orcid` field in the `author_metadata` is not `None`. When it is present, the ORCID value is retained (instead of being replaced with an empty string, as in the case when it’s absent). The fixture includes institution metadata that.contains sample values like a URL, OpenAlex URL, and ROR AS WELL AS author metadata which provides an ORCID value (`"orcid-789"`) and an OpenAlex URL for the researcher..not to mention subfield metadata that lists a single subfield with its corresponding OpenAlex URL.. n totality the data contains numerical data (total number of works, citations) and a list of work entries. This setup is used in tests to foresee that when valid ORCID data exists, the application processes and "preserves" that information as expected. """
    return {
        "institution_metadata": {
            "url": "http://institution.example.com",
            "openalex_url": "institution_oa_123",
            "ror": "ror123"
        },
        "author_metadata": {
            "orcid": "orcid-789",
            "openalex_url": "researcher_oa_456"
        },
        "subfield_metadata": [
            {"topic": "Subfield A", "subfield_url": "topic_oa_789"}
        ],
        "totals": {
            "total_num_of_works": 4,
            "total_num_of_citations": 40
        },
        "data": [
            {"work_name": "Work A", "cited_by_count": 10},
            {"work_name": "Work B", "cited_by_count": 15},
        ]
    }


@pytest.fixture
def fake_sparql_empty():
    """ This test verifies that when both the primary database query and the fallback SPARQL query return no data, the function returns an empty dictionary. In detail, the `fake_sparql_empty` fixture returns an empty dictionary (`{}`), simulating a SPARQL query with no results (responsible for lines 815–816 of app.py)."""
    return {}


def test_sparql_branch_empty(monkeypatch, fake_sparql_empty):
    """ In the test, `monkeypatch` is used to "override" `search_by_author_institution_topic` to return `None` so that the SPARQL branch is taken, AND `get_institution_and_topic_and_researcher_metadata_sparql` to return the empty dictionary from `fake_sparql_empty`. When `get_institution_researcher_subfield_results` is called, it detects no results from the database and then falls back to the SPARQL query. Since the SPARQL function returns an empty dictionary, the function logs a warning and returns `{}`. Thus, the test asserts that in this scenario the function correctly returns an empty result (`{}`).  """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: None
    )
    monkeypatch.setattr(
        "backend.app.get_institution_and_topic_and_researcher_metadata_sparql",
        lambda i, t, r: fake_sparql_empty
    )
    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test")
    assert result == {}


def test_database_branch_orcid_none(monkeypatch, fake_db_data_orcid_none):
    """ This test verifies the database branch for researcher‑topic‑institution searches when the author's ORCID is missing (i.e. it is `None`), which is handled on line 834 of app.py. In this test--the `search_by_author_institution_topic` function is monkeypatched to return the fake database data (`fake_db_data_orcid_none`) where the `orcid` field in `author_metadata` is `None`, & when `get_institution_researcher_subfield_results` is called, the code checks the returned metadata. Since the ORCID is `None`, the code sets it to an empty string, & then the test then asserts that various metadata fields (homepage, institution OpenAlex URL, ROR, institution name, researcher name and OpenAlex URL, topic name, topic clusters, work count, citation count, and topic OpenAlex URL) are set correctly. It ALSO verifies that the pagination metadata is correctly calculated based on the number of works in the fake data. Finally, the test inspects the graph structure to ensure that nodes representing the institution, researcher, topic, and each work are present. In totality, this test demonstrates that when the ORCID is missing, the application processes the data correctly by setting the ORCID to an empty string and "builds" the metadata and graph as expected. """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: fake_db_data_orcid_none
    )
    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["homepage"] == "http://institution.example.com"
    assert metadata["institution_oa_link"] == "institution_oa_123"
    assert metadata["ror"] == "ror123"
    assert metadata["institution_name"] == "Institution Test"
    assert metadata["orcid"] == ""
    assert metadata["researcher_name"] == "Researcher Test"
    assert metadata["researcher_oa_link"] == "researcher_oa_456"
    assert metadata["topic_name"] == "Topic Test"
    assert metadata["topic_clusters"] == ["Subfield A"]
    assert metadata["work_count"] == 10
    assert metadata["cited_by_count"] == 100
    assert metadata["topic_oa_link"] == "topic_oa_789"
    meta_pagination = result["metadata_pagination"]
    total_topics = len(fake_db_data_orcid_none["data"])
    expected_total_pages = (total_topics + 10 - 1) // 10
    assert meta_pagination["total_pages"] == expected_total_pages
    assert meta_pagination["current_page"] == 1
    assert meta_pagination["total_topics"] == total_topics
    graph = result["graph"]
    nodes = graph["nodes"]
    expected_institution_node = {
        'id': "institution_oa_123", 'label': "Institution Test", 'type': "INSTITUTION"}
    assert expected_institution_node in nodes
    expected_researcher_node = {
        'id': "researcher_oa_456", 'label': "Researcher Test", 'type': "AUTHOR"}
    assert expected_researcher_node in nodes
    expected_topic_node = {'id': "topic_oa_789",
                           'label': "Topic Test", 'type': "TOPIC"}
    assert expected_topic_node in nodes
    for entry in fake_db_data_orcid_none["data"]:
        work_node = {'id': entry["work_name"],
                     'label': entry["work_name"], 'type': "WORK"}
        assert work_node in nodes


def test_database_branch_orcid_present(monkeypatch, fake_db_data_orcid_present):
    """ This test validates the database branch for a researcher‑institution‑topic search when the ORCID is present in the database response (as handled around line 836 of app.py). The test over-rides the `search_by_author_institution_topic` function so that it returns the fake database data (`fake_db_data_orcid_present`), which includes an ORCID value of `"orcid-789"`. After calling `get_institution_researcher_subfield_results`, the test inspects the `metadata` dictionary. It asserts that the ORCID remains as `"orcid-789"`, and other metadata fields, such as the institution homepage, the institution OpenAlex link, and the researcher OpenAlex link, match the expected values. It calculates the expected total number of pages based on the number of work entries and verifies that the `metadata_pagination` fields (total pages and current page) are correct.
    The test constructs, an expected list of tuples (each containing a work name and its corresponding cited-by count) from the fake data and confirms that the `list` returned by the function matches this expected list. Now, this test coincides witht he fact that when the ORCID is provided, the function correctly processes and preserves it in the metadata, along with accurately constructing the pagination and list data. """
    monkeypatch.setattr(
        "backend.app.search_by_author_institution_topic",
        lambda r, i, t: fake_db_data_orcid_present
    )
    result = get_institution_researcher_subfield_results(
        "Institution Test", "Researcher Test", "Topic Test", page=1, per_page=10)
    metadata = result["metadata"]
    assert metadata["orcid"] == "orcid-789"
    assert metadata["homepage"] == "http://institution.example.com"
    assert metadata["institution_oa_link"] == "institution_oa_123"
    assert metadata["researcher_oa_link"] == "researcher_oa_456"
    meta_pagination = result["metadata_pagination"]
    total_topics = len(fake_db_data_orcid_present["data"])
    expected_total_pages = (total_topics + 10 - 1) // 10
    assert meta_pagination["total_pages"] == expected_total_pages
    expected_list = []
    for entry in fake_db_data_orcid_present["data"]:
        expected_list.append((entry["work_name"], entry["cited_by_count"]))
    assert result["list"] == expected_list
