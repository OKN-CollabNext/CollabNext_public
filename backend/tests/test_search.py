from unittest.mock import patch
import pytest
from unittest.mock import patch, MagicMock

# Meanwhile, we can get started on importing the specific functions for
# searching that we "would like" to test and then we can import everything
# and alternatively we can test individually.
from backend.app import (
    search_by_author,
    search_by_institution,
    search_by_topic,
    execute_query
)


@pytest.fixture
def mock_execute_query():
    """
    A fixture that follows up on the patch `app.execute_query` regularly to make it
    so that yea, we can get more specifics on query execution infra-structure in order
    to prevent "actual" Database calls.
    """
    with patch("backend.app.execute_query") as mock:
        yield mock


@patch("backend.app.execute_query")
def test_search_by_author_found(mock_exec):
    """
    And this is how we test the two calls we test them locally directly from source. These are the two calls:
    1) Once we get_author_ids(...) then we expect to see a row with e.g. a list of dictionaries.
    2) Alternatively we can do the call for search_by_author(...) wherein we expect the final data in this backend testing suite.
    """
    # Let's look at the code get_author_ids(...) -> results[0][0] which does, it returns something like [ { "author_id": "4626" }]
    # And then we will be ready to search by the author we can search, and get the results[0][0] and then we can look at this result -> returns { "author_metadata": {...}, "data": [... ] }
    # And THEN the code get_author_ids(...) -> results[0][0] -> returns something like [ { "author_id": "8979" } ] this.
    # Then when we search by author(...) we get finally results[0][0] which "leads us" to the { "author_metadata": {...}, "data": [... ] }
    mock_exec.side_effect = [
        # 1) Perhaps we can try switching the return value for get_author_ids(author_name), on.
        [
            (
                # This is the data for JavaScript Object Notation.!
                [{"author_id": "1234"}],
            )
        ],  # That is, the results is a list of one row that row is a tuple AND that tuple..has a first element that is a dict list
        # 2) Return value for search_by_author(%s) "it is".
        [
            (
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
                },
            )
        ]
    ]

    from backend.app import search_by_author
    result = search_by_author("Lew Lefton")

    assert result is not None
    assert "author_metadata" in result
    assert len(result["data"]) == 2


def test_search_by_author_not_found(mock_execute_query):
    """
    And then we have some tests that search_by_author returns when it returns None when the Database, has no results. For instance let's say the author is in a different time zone and we see that the author's search result that is should return None if no Database results exist.
    """
    # And, we so mock the Database to return an empty result and or the value of None.
    mock_execute_query.return_value = None
    result = search_by_author("Unknown Name")
    assert result is None, "Should return None if no DB results"


@patch("backend.app.execute_query")
def test_search_by_institution(mock_execute_query):
    """
    In any way we can integrate tests that return the search_by_institution data properly.
    """
    mock_execute_query.side_effect = [
        # The first call -> get_institution_id("MyUniversity")
        [
            ({"institution_id": 1415},)
        ],
        # The second call -> search_by_institution("1415")
        [
            (
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
                    ]
                },
            )
        ]
    ]
    from backend.app import search_by_institution
    result = search_by_institution("MyUniversity")
    assert result is not None
    assert "institution_metadata" in result
    assert result["institution_metadata"]["institution_name"] == "MyUniversity"


def test_search_by_topic(mock_execute_query):
    """
    I saw both of these tests search_by_topic and return some object with the raw Database fields.
    """
    mock_execute_query.return_value = [
        [{
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
                {"institution_name": "State University", "num_of_authors": 100},
            ]
        }]
    ]
    # Call directly the search_by_topic:
    result = search_by_topic("Chemistry")
    # "Expect" to see the keys for the dictionary in its raw form:
    assert result is not None
    assert "subfield_metadata" in result
    assert "totals" in result
    assert "data" in result
    # No longer do we use this test to get "graph" or "list" here because that is only in get_subfield_results.
