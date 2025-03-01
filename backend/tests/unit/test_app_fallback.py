import pytest
from unittest.mock import patch, MagicMock
from backend.app import (
    app,
    initial_search,
    get_researcher_result,
    get_institution_results,
    get_researcher_and_subfield_results,
)

""" Next thing--we need to build in a methodology as a fixture in order to generate this testing client for the app that we are running by using Flask. When we run this app we will understand that we have to clean up the comments accordingly and make sure that it is possible to do all the expansions that Prof. Lew is asking for..and in order to do this we need a testing client. These testing files are designed to modularize our testing methodology. """


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

# -----------------------------------------------------------------------------
# And that's precisely what I intend to do here. I want to test out what is the initial-search, we call this a branch because it's the endpoint error branch that we call /initial-search and that's the "place" where we simulate an exception.
# -----------------------------------------------------------------------------


def test_initial_search_exception(client):
    """
    Very similarly to the way that we thought about how this project should be executed, we had about thirty ideas for how this should play out and we did that by mistake but in the end we realized that the try / except type of block in the initial_search() was going to return an error response.
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

# -----------------------------------------------------------------------------
# Here it is, the get_research_result we do that for the researcher. WE do this in order to get the tests for the logic, we call these dummy variables. Do we want to give them a separate name? No, but we can give them separate files. That's something that should ideally "fall into place" in the sense that we can always add new results to the system.
# -----------------------------------------------------------------------------


def test_get_researcher_result_fallback_success():
    """
    THen, we have already decided what topics, what results we're going to get from the researcher. This should sort of serve as a a "database model" in the sense that then, when we search by the author and when that returns None, then we know that the get_author_metadata_sparql is called.
    It's like this, all of the returning of the valid metadata as well as all of the function calls to list_given_researcher_institution, these are going to return dummy values. Then we also know that the get_researcher_result function should be returning a structure with metadata & graph & ..list.
    """
    dummy_metadata = {
        "oa_link": "dummy_oa",
        "name": "Test Author",
        "current_institution": "Test Institution"
    }
    dummy_list = [("topic1", 5)]
    dummy_graph = {"nodes": [{"id": "Test Institution", "label": "Test Institution", "type": "INSTITUTION"}],
                   "edges": []}
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
    And that's what we get when we do, we are able to analyze the resulst we get from all this MultiRAG process..in order to analyze these we need to understand how we can test and get the results from the researcher as a fallback..what if the database search doesn't return any useful data..what if the search_by_author on the database and or the fallback function for SPARQL which we call get_author_Metadata_sparql thing don't return any data that we find useful..then we have to acknowledge that the get_researcher_result thing isn't going to do anything other than return an empty dictionary.
    """
    with patch("backend.app.search_by_author", return_value=None), \
            patch("backend.app.get_author_metadata_sparql", return_value={}):
        result = get_researcher_result("Test Author")
        assert result == {}

# -----------------------------------------------------------------------------
# So that brings us to this..we have to understand the way that we can get a "technical lead" on this whole test thing..the test idea is that we have built in some logic for the fallback functions that we have in the get_institutioN_results function.
# -----------------------------------------------------------------------------


def test_get_institution_results_fallback_success():
    """
    So that's what we get..we understand that we're looking for a subset of our current institution data..when search_by_institution returns None then we know that we have to use the get_institution_metadata_sparql thing and we know that with a valid metadata dictionary as well as a dummy graph / list rom the list_given_instituion, then we have to get the institution results and we know that that result should return the structure that we expect.
    """
    dummy_metadata = {
        "ror": "dummy_ror",
        "name": "Dummy Inst",  # this is the key we expect from the get_institutioN_results
        # it's worth noting that it's spelled "works_count" not workscount or something
        "works_count": "50",
        "cited_count": "100",  # And what we know is that we have this idea that the cited count, the count of things that we cite is spelled cited_count
        "homepage": "dummy_homepage",
        "author_count": "20",  # And then we have this count of people as our key
        # And here we have this requirement for the argument that is our third argument, we do require a key to exist.
        "oa_link": "dummy_oa_link",
        "hbcu": False
    }
    dummy_list = [("subfield1", 10)]
    dummy_graph = {"nodes": [{"id": "dummy_inst", "label": "Dummy Inst", "type": "INSTITUTION"}],
                   "edges": []}
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
    And that's what we do, we then do the function search_by_institution which returns None and alternatively we have this SPARQL fallback function that might yield an empty dictionary but in the end we have to remember that get_institution_results is going to return an empty dictionary. Please feel free to fill in more results according to the database instructions.
    """
    with patch("backend.app.search_by_institution", return_value=None), \
            patch("backend.app.get_institution_metadata_sparql", return_value={}):
        result = get_institution_results("Dummy Inst")
        assert result == {}

# -----------------------------------------------------------------------------
# So here they are, the tests for the logic for falling back in the results section of the get_researcher_and_subfield that we get, and we get that we know that we can have a "technical lead" that tells us that the subset of the current data..isn't enough.
# -----------------------------------------------------------------------------


def test_get_researcher_and_subfield_results_fallback_success():
    """
    And that's what happens when we run the frontend..we have to understand that the errors we get whether it's compiling with problems or otherwise, we have to search by the author topic and when. we do that might return a value of None in which case, we have to fall back to using the query with SPARQL . I have all these fallback functiomns wherein, with dummy metadata for instance and listing the given researcher topic values being provided, I actually know that get_researcher_and_subfield_results is "going" to return a valid structure.
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
    dummy_graph = {"nodes": [{"id": "dummy_topic", "label": "Test Topic", "type": "TOPIC"}],
                   "edges": []}
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
    Alternatively, if search_by_author_topic returns None and the fallback function for SPARQL is returning an empty dictionary tyhen we know that the results for the getting researcher and subfield will return an empty dictionary. Ideally the database does return records however some help is needed from the domain owner in updating A records.
    """
    with patch("backend.app.search_by_author_topic", return_value=None), \
            patch("backend.app.get_topic_and_researcher_metadata_sparql", return_value={}):
        result = get_researcher_and_subfield_results(
            "Test Author", "Test Topic")
        assert result == {}
