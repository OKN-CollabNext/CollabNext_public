import pytest
""" For instance, it is "worth noting" that this is how we test calls in general we test them locally directly from source. For instance, when we are looking for whether or not an author has been found, we do the test_search_by_author_found method. 1) One upon a time, we get_author_ids(...). Then, we expect to see a row with e.g. a list of dictionaries. 2) Alternatively we can do the call for search_by_author(...) wherein we expect the final data in this backend testing suite. """
from unittest.mock import patch
from backend.app import (
    search_by_author,
    search_by_author_institution_topic,
    search_by_author_institution,
    search_by_institution_topic,
    search_by_author_topic,
    search_by_topic,
    search_by_institution,
)
""" Let's look at the code get_author_ids(...) -> results[0][0] which does, it returns something like [ { "author_id": "4626" }]..then, we are ready to search by the author. We can search, and get the results[0][0] and then we can look at this result->returns { "author_metadata": {...}, "data": [... ] } and THEN the code get_author_ids(...) -> results[0][0] -> returns something like [ { "author_id": "8979" } ] this. Then when w search by author(...) we get finally results[0][0] which "leads us" to the { "author_metadata": {...}, "data": [... ] }...with the propensity for some "side effects" when we search by author.  """


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"author_metadata": {"dummy": "data"}}]])
def test_search_by_author_success(mock_exec, mock_get_author_ids):
    result = search_by_author("Test Author")
    assert result == {"author_metadata": {"dummy": "data"}}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_no_ids(mock_get_author_ids):
    result = search_by_author("Test Author")
    assert result is None


""" 1) And by side effects I don't mean the mock_exec.side_effect. I mean how we can try, switching the return value for get_author_ids(author_name), onward. This is the notation, the data for the JavaScript Object Notation.! This is the test search_by_author_institution_topic. That is, the results is a list of one row, that row is a tuple AND that tuple..has a first element that is a dict list. 2) Return the value for search_by_author(%s) "it is". """


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result"}]])
def test_search_by_author_institution_topic_success(mock_exec, mock_get_institution_id, mock_get_author_ids):
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
def test_search_by_author_institution_topic_no_institution_id(mock_get_institution_id, mock_get_author_ids):
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result is None


""" And then we have some patches, and then we have some tests that search_by_author returns when returns None when the Database has no results. For instance let's say the author is in a different time zone and we see that the author's search result that is should return None if no Database results exist. We search_by_author_institution that's our test.  """


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result2"}]])
def test_search_by_author_institution_success(mock_exec, mock_get_institution_id, mock_get_author_ids):
    result = search_by_author_institution("Author", "Institution")
    assert result == {"dummy": "result2"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_institution_no_author_ids(mock_get_author_ids):
    result = search_by_author_institution("Author", "Institution")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_no_institution_id(mock_get_institution_id, mock_get_author_ids):
    result = search_by_author_institution("Author", "Institution")
    assert result is None


""" And, we so mock the database to return an empty result and or if the value should be set to None. """


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result3"}]])
def test_search_by_institution_topic_success(mock_exec, mock_get_institution_id):
    result = search_by_institution_topic("Institution", "Topic")
    assert result == {"dummy": "result3"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_topic_no_institution_id(mock_get_institution_id):
    result = search_by_institution_topic("Institution", "Topic")
    assert result is None


""" In ""any way" we can integrate tests that return the search_by_institution data properly.  """


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"dummy": "result4"}]])
def test_search_by_author_topic_success(mock_exec, mock_get_author_ids):
    result = search_by_author_topic("Author", "Topic")
    assert result == {"dummy": "result4"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_topic_no_author_ids(mock_get_author_ids):
    result = search_by_author_topic("Author", "Topic")
    assert result is None


""" This is how we search we have that the first call -> get_institution_id("MyUniversity"), and then we have that the second call is -> search_by_institution("1415"). Furthermore we can test search_by_topic. """


@patch("backend.app.execute_query", return_value=[[{"dummy": "result5"}]])
def test_search_by_topic_success(mock_exec):
    result = search_by_topic("Topic")
    assert result == {"dummy": "result5"}


@patch("backend.app.execute_query", return_value=None)
def test_search_by_topic_no_result(mock_exec):
    result = search_by_topic("Topic")
    assert result is None


""" And then we can test search_by_institution. I saw both of these tests search_by_topic and returned some object with the raw Database fields. """


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result6"}]])
def test_search_by_institution_success(mock_exec, mock_get_institution_id):
    result = search_by_institution("Institution")
    assert result == {"dummy": "result6"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_no_institution_id(mock_get_institution_id):
    result = search_by_institution("Institution")
    assert result is None


""" After all this, I can call directly the search_by_topic : and then "expect" to see the keys for the dictionary in their raw form: no longer do we use this test to get "graph" or "list' here because that, is only in get_subfield_results. """
