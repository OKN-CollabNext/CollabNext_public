"""
Search Workflow Integration Test Suite

This module comprises integration tests for the application's search workflows.
It focuses on the following search functionalities:
  - search_by_author
  - search_by_institution
  - search_by_topic
  - search_by_author_institution
  - search_by_author_topic
  - search_by_institution_topic
  - search_by_author_institution_topic
  - Fallback mechanisms for search functions when primary queries fail
"""

import pytest
from unittest.mock import patch
from backend.app import (
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
def test_search_by_author_param(mock_exec, author_name, get_author_ids_result, search_by_author_result, final_expected):
    """ The "AuthorNotFound" scenario is the FALLBACK LOGIC TEST.
    The search by author parameter(s) test is directly responsible for verifying that lines 147-148 of `app.py` correctly handle the case when no author IDs are found by returning None and logging a warning..such that the function only proceeds to query further when an author ID does exist.
     So in that part of the code from lines 147-148 of apppy the function is calling `get_author_ids(author_name) to fetch the author's IDs, and checks whether any IDs were returned..if none were found THEN it logs a warning and returns `None`.
     The idea is to utilize parameterized inputs to simulate two scenarios:
     (1) Either the author is found..if AuthorFound (exists) then the test, passes a non-None `get_author_ids_result` i.e.a. list, with a dictionary containing "author_id": "1234"..this makes the code continue past the check. The subsequent mock, then returns a search_by_author_result (which includes an "author_metadata" key). The test 'also" asserts that the final result is not `None` and then that it does contain, the "author_metadata".
     If AuthorNotFound, then the test passes `None` as the `get_author_ids_result`. This is what causes the condition `if not author_ids: ` that is from lines 147-148 to be true, so that the function "right away" returns `None` which, is corroborated and confirmed via the test, on the behavior of "these two scenarios". """
    if get_author_ids_result is None:
        mock_exec.side_effect = [None]
    else:
        mock_exec.side_effect = [[(get_author_ids_result)], [
            (search_by_author_result)]]
    result = search_by_author(author_name)
    if final_expected:
        assert result is not None
        assert "author_metadata" in result
    else:
        assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result"}]])
def test_search_by_author_institution_topic_success(
    mock_execute_query,
    mock_get_institution_id,
    mock_get_author_ids
):
    """ This is part of the focus of the function; it focuses on the part of the function (lines 183-184 in app.py) where, after retrieving the author and institution Ids, the function executes a SQL query via `execute_query` and then, returns the result..the "way that this works" is that we patch dependencies..we patch the get_author_ids to return a list with one dictionary containing an author ID called `[{"author_id": "id_001"}]. We also patch `get_institutioN_id` to return an institution ID 123, and then patch execute_query to return a nested list `[[{"dummy": "result"}]].
    The function search_by_author_institution_topic now "returns" and uses the patched `get_author_ids` and `get_institution_id` to fetch the IDs required. It then calls execute_query with these IDs as well as the topic..that means that "according" to the "implementation" specifically from and in lines 183-184, it extracts the first element from the first row of the returned query result and returns it.
    Furthermore, the test asserts that the function returns {"dummY": "result"}, confirming that the SQL query execution and result extraction are working as expected. In short, this test confirms that when valid author and institution IDs are provided and the SQL query returns data, the function correctly processes and returns the result as specified in the following lines of app.py: 183-184. """
    topic = "TestTopic"
    result = search_by_author_institution_topic("Author", "Institution", topic)
    # We're left with the final data
    assert result == {"dummy": "result"}, "Expected the dummy result from DB"
    # Alternately encourage correct call arguments to execute_query
    mock_execute_query.assert_called_once()
    args, kwargs = mock_execute_query.call_args
    # Informally, the query and parameters are the first two elements
    assert topic in args[1], "Topic should be among query parameters"


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result2"}]])
def test_search_by_author_institution_success(
    mock_execute_query,
    mock_get_institution_id,
    mock_get_author_ids
):
    """ We know that when real live author and institution IDs are provided, the function reaches the part where it executes the SQL query and returns the expected result. Specifically, Lines 206-207 in app.py extract the first element of the query result i.e. results[0][0] after. asuccessful call to execute_queryl. The details of the patching are that `get_author_ids` is patched to return `[{"author_id": "id_001"}], so the function uses "`id_001`" as the author Id. Also, `get_institution_id` is patched to return `123`, which makes sure that the institution ID is valid. `execute_query` is patched to return `[[{"dummY": "result2"}]]`, simulating a successful database response.
    What is the execution flow? The function search_by_author_institution uses these patched values, calls execute-query, and then, according to lines 206-207, it returns the first item of the query result. The "rest of the test"..asserts, that the returned value is `{"dummY"; "result2"}`,  atching the expected result from the patched query response. """
    author = "Author"
    institution = "Institution"
    result = search_by_author_institution(author, institution)
    assert result == {"dummy": "result2"}, "Expected the dummy 'result2' data"
    mock_execute_query.assert_called_once()
    called_query, called_params = mock_execute_query.call_args[0]
    assert "search_by_author_institution" in called_query, "Should call the correct SQL function"
    assert called_params == (
        "id_001", 123), "Should pass correct author_id and institution_id"


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result3"}]])
def test_search_by_institution_topic_success(mock_execute_query, mock_get_institution_id):
    """
    The function fo r searching by institution and topic behaves correctly when valid data is returned. In particular, Lines 221-222 of app.py perform the following steps: (1) Retrieve the Institution ID: The function call(ed) get_institution_id("Institution"), which--via the patch--returns `123`.
    With a valid institution ID, we execute the Database Query; it then calls `execute_query` with a query (using the institution ID and the topic "Topic") and the patched `execute_query` returns `[[{"dummy": "result3"}]]`. I extract and return teh result; "the function," extracts (and returns?) the first element from the returned nested list (i.e., `results[0][0]`) and returns it. In this case, it returns `{"dummy": "result3"}`. "The test asserts" that the final result matches thie expeted output, confirming that lines 221-222 are handling a successful search by institution and topic correctly.
    """
    institution = "MyInstitution"
    topic = "MyTopic"
    result = search_by_institution_topic(institution, topic)
    assert result == {
        "dummy": "result3"}, "Expected the dummy 'result3' from DB"
    mock_execute_query.assert_called_once()
    query_str, params = mock_execute_query.call_args[0]
    assert "search_by_institution_topic" in query_str, "Should be calling the correct stored function"
    assert params == (
        123, topic), "Should pass institution_id and topic correctly"


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"dummy": "result4"}]])
def test_search_by_author_topic_success(mock_execute_query, mock_get_author_ids):
    """
    This test checks that the `search_by_author_topic` function correctly processes a successful query when both the author exists and the query returns valid data. Specifically, it verifies the behavior of lines 239–240 in app.py, which are responsible for extracting the final result from the SQL query response.
    Specifically, get_author_ids is patched to return a list with one dictionary containing "author_id": "id_001", so the function uses "id_001" as the author's identifier. Also, execute_query is patched to return a nested list [[{"dummy": "result4"}]], simulating a successful database query.
    With these patches in place, search_by_author_topic("Author", "Topic") calls the patched functions. After retrieving the author ID, it executes the query. Lines 239–240 then extract the first element of the first row of the result, which is {"dummy": "result4"}, and return it. Then "following this" the test, asserts that the returned result exactly matches {"dummy": "result4"}, confirming that the function correctly processes the query result as "intended".
    """
    author = "MyAuthor"
    topic = "MyTopic"
    result = search_by_author_topic(author, topic)
    assert result == {"dummy": "result4"}, "Expected 'result4' from DB"
    mock_execute_query.assert_called_once()
    _, params = mock_execute_query.call_args[0]
    # That's what most of the typical stuff for the backend is going, to be (author_id, topic)
    assert params == ("id_001", topic)

###############################################################################
# FALLBACK LOGIC TESTS
###############################################################################


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_topic_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    """
    So we know that the search_by_author_institution_topic correctly handles the case when no institution ID is found but we still write a test case because, specifically the lines 177-178 that are referenced in app.py by this test function check the result of calling get_institution_Id. What this means is that we have a mock setup..the test patches get_author_ids to return a valid list with an author Id. It then patches the get_institution_id to return None, simulating "a" situation where the institution lookup "fails".
    What is the expected behavior? Well, when get_institution_id returns None, the function should log a warning and immediately return None without proceeding further. This behavior corresponds to the check at lines 177-178.
    The test assertion is that the test "is calling" search_by_author_institution_topic with dummy parameters and asserts that the result is `None`, confirming that the function handles the missing institution ID as expected.
    """
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result is None, "Expected None result because institution_id is None"


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    """
    This test verifies the behavior of the search_by_author_instituion function when the institution ID cannot be found. Specifically, lines 200-201 in app.py check the result of calling get_Instituion_id: the mock setup is that the get_author_ids, is patched to return a valid list containing an author ID `[{"author_id": "id_001"}]`.
    `get_institution_id` is patched to return `None`, simulating the failure to retrieve a valid institution ID.
    The function follows the execution flow of the search_by_author_institution "which" calls get_institutioN_id and finds that it returns `None`. According to lines 200-201, when the institution ID is None, the function logs a warning and almost instantaneously returns `None` without attempting to execute a further queyr.
    The test asserts that the result of the function is `None`, confirming that the missing institution ID is handled correctly.
    """
    result = search_by_author_institution("Author", "Institution")
    assert result is None, "Expected None result because institution_id is None"


def test_get_researcher_and_subfield_results_fallback_no_results():
    """
    This test verifies the fallback behavior in the `get_researcher_and_subfield_results` function when both the database query as well as the SPARQL query fail to return useful data. Specifically, it targets lines 587–588: after calling search_by_author_topic(researcher, topic), if the result is None, the function logs that no database results were found and THEN calls get_topic_and_researcher_metadata_sparql(topic, researcher).
At line 586, the SPARQL result is checked. If the SPARQL query returns an empty dictionary ({}), then, as specified in lines 587–588, the function logs a warning ("No results found in SPARQL for researcher and topic") and "after" that returns an empty dictionary ({}).
    The test patches: `search_by_author_topic` to return None, simulating that the database search did not find any data AS WELL AS `get_topic_and_researcher_metadata_sparql` to return `{}`, simulating that the SPARQL fallback did not yield any results.
    Thus we can confidently say that with these conditions, the function should hit the branch in lines 587–588 and return {}. The test then asserts that the final result is indeed an empty dictionary.
    """
    with patch("backend.app.search_by_author_topic", return_value=None), \
            patch("backend.app.get_topic_and_researcher_metadata_sparql", return_value={}):
        result = get_researcher_and_subfield_results(
            "Test Author", "Test Topic")
        assert result == {}, "Expected empty dict fallback when both DB and SPARQL fail"


###############################################################################
# SCHEMA VALIDATION TESTS
###############################################################################


def test_institution_search_result_schema():
    """
    This test validates that the search_by_institution function (specifically, lines 264–265 of app.py) returns a result that follows the expected schema. What we're doing is mocking the underyling data retrieval: we patch get_institution_id to return a dummy institution ID (123) as well as execute_query to return a predefined mock_result containing an "institution_metadata" dictionary with keys "institution_name", "openalex_url", "num_of_authors", and "num_of_works" AND we patch a "data" list with dictionaries, each expected to include "topic_subfield" and "num_of_authors"..the test then calls search_by_institution("Test University") and asserts that the result contains the keys "institution_metadata" and "data" & the "institution_metadata" object includes the required fields & each item in the "data" list has the expected keys.
    """
    mock_result = {
        "institution_metadata": {
            "institution_name": "Test University",
            "openalex_url": "https://openalex.org/institution/5678",
            "num_of_authors": 50,
            "num_of_works": 100,
        },
        "data": [
            {"topic_subfield": "CompSci", "num_of_authors": 25},
            {"topic_subfield": "Biology", "num_of_authors": 20},
        ],
    }
    with patch("backend.app.get_institution_id", return_value=123), \
            patch("backend.app.execute_query", return_value=[(mock_result,)]):
        result = search_by_institution("Test University")
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "institution_metadata" in result, "Key 'institution_metadata' missing"
        assert "data" in result, "Key 'data' missing"
        metadata = result["institution_metadata"]
        assert "institution_name" in metadata
        assert "openalex_url" in metadata
        assert "num_of_authors" in metadata
        assert "num_of_works" in metadata
        for item in result["data"]:
            assert "topic_subfield" in item
            assert "num_of_authors" in item


def test_topic_search_result_schema():
    """
    This test "shows" that the output of the search_by_topic function adheres and "sticks" to the "expected" schema. In the code (specifically lines 249–250 of app.py), after executing the SQL query, the function checks for results and then returns the first element of the first row (i.e. results[0][0]). The returned value is "expected" to be a dictionary with "specific" keys.
    What we do is, we mock the query result. The test, sets up a mock_result dictionary with three keys: "subfield_metadata": A list of dictionaries, each containing "topic" and "subfield_url"..as well as "totals": A dictionary with total counts ("total_num_of_works", "total_num_of_citations", "total_num_of_authors")...and "last on the list" we "have" "data": a list of dictionaries with keys "institution_name" and "num_of_authors".
    It patches the execute_query function to return a nested list containing mock_result, mimicking the structure expected from a database query.
    The test calls search_by_topic("Chemistry") and asserts "that" the returned dictionary contains the keys "subfield_metadata", "totals", and "data", that each item in "subfield_metadata" has both "topic" and "subfield_url", that the "totals" dictionary includes all the expected total count keys AND, that every entry in "data" includes "institution_name" and "num_of_authors".
    """
    mock_result = {
        "subfield_metadata": [
            {"topic": "Chemistry", "subfield_url": "https://openalex.org/subfield/123"}
        ],
        "totals": {
            "total_num_of_works": 999,
            "total_num_of_citations": 3000,
            "total_num_of_authors": 200
        },
        "data": [
            {"institution_name": "Tech Labs University", "num_of_authors": 50},
            {"institution_name": "State University",     "num_of_authors": 100},
        ]
    }
    with patch("backend.app.execute_query", return_value=[(mock_result,)]):
        result = search_by_topic("Chemistry")
        assert isinstance(
            result, dict), "search_by_topic should return a dictionary"
        assert "subfield_metadata" in result, "Missing 'subfield_metadata' key"
        assert "totals" in result, "Missing 'totals' key"
        assert "data" in result, "Missing 'data' key"
        for item in result["subfield_metadata"]:
            assert "topic" in item
            assert "subfield_url" in item
        totals = result["totals"]
        assert "total_num_of_works" in totals
        assert "total_num_of_citations" in totals
        assert "total_num_of_authors" in totals
        for item in result["data"]:
            assert "institution_name" in item
            assert "num_of_authors" in item
