"""
Search Workflow Tests

This file contains integration tests for the search workflows in the application.
Tests include:
- search_by_author
- search_by_institution
- search_by_topic
- search_by_author_institution
- search_by_author_topic
- search_by_institution_topic
- search_by_author_institution_topic
- Fallback logic for search functions
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.app import (
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
    """
    Test search_by_author when no author IDs are found.
    """
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
    """
    Test successful search by author, institution, and topic.
    """
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result == {"dummy": "result"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_institution_topic_no_author_ids(mock_get_author_ids):
    """
    Test search_by_author_institution_topic when no author IDs are found.
    """
    result = search_by_author_institution_topic(
        "Author", "Institution", "Topic")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_topic_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    """
    Test search_by_author_institution_topic when no institution ID is found.
    """
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
    """
    Test successful search by author and institution.
    """
    result = search_by_author_institution("Author", "Institution")
    assert result == {"dummy": "result2"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_institution_no_author_ids(mock_get_author_ids):
    """
    Test search_by_author_institution when no author IDs are found.
    """
    result = search_by_author_institution("Author", "Institution")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_author_institution_no_institution_id(
    mock_get_institution_id,
    mock_get_author_ids
):
    """
    Test search_by_author_institution when no institution ID is found.
    """
    result = search_by_author_institution("Author", "Institution")
    assert result is None


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result3"}]])
def test_search_by_institution_topic_success(mock_exec, mock_get_institution_id):
    """
    Test successful search by institution and topic.
    """
    result = search_by_institution_topic("Institution", "Topic")
    assert result == {"dummy": "result3"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_topic_no_institution_id(mock_get_institution_id):
    """
    Test search_by_institution_topic when no institution ID is found.
    """
    result = search_by_institution_topic("Institution", "Topic")
    assert result is None


@patch("backend.app.get_author_ids", return_value=[{"author_id": "id_001"}])
@patch("backend.app.execute_query", return_value=[[{"dummy": "result4"}]])
def test_search_by_author_topic_success(mock_exec, mock_get_author_ids):
    """
    Test successful search by author and topic.
    """
    result = search_by_author_topic("Author", "Topic")
    assert result == {"dummy": "result4"}


@patch("backend.app.get_author_ids", return_value=None)
def test_search_by_author_topic_no_author_ids(mock_get_author_ids):
    """
    Test search_by_author_topic when no author IDs are found.
    """
    result = search_by_author_topic("Author", "Topic")
    assert result is None


@patch("backend.app.execute_query", return_value=[[{"dummy": "result5"}]])
def test_search_by_topic_success(mock_exec):
    """
    Test successful search by topic.
    """
    result = search_by_topic("Topic")
    assert result == {"dummy": "result5"}


@patch("backend.app.execute_query", return_value=None)
def test_search_by_topic_no_result(mock_exec):
    """
    Test search_by_topic when no results are found.
    """
    result = search_by_topic("Topic")
    assert result is None


@patch("backend.app.get_institution_id", return_value=123)
@patch("backend.app.execute_query", return_value=[[{"dummy": "result6"}]])
def test_search_by_institution_success(mock_exec, mock_get_institution_id):
    """
    Test successful search by institution.
    """
    result = search_by_institution("Institution")
    assert result == {"dummy": "result6"}


@patch("backend.app.get_institution_id", return_value=None)
def test_search_by_institution_no_institution_id(mock_get_institution_id):
    """
    Test search_by_institution when no institution ID is found.
    """
    result = search_by_institution("Institution")
    assert result is None


###############################################################################
# FALLBACK LOGIC TESTS
###############################################################################

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
    if "institution_oa_link" not in dummy_metadata:
        pytest.fail(
            "Missing 'institution_oa_link' in test data; skipping to avoid KeyError.")
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
# SCHEMA VALIDATION TESTS
###############################################################################

def test_author_search_result_schema():
    """
    Test that the author search result follows the expected schema.
    """
    mock_result = {
        "author_metadata": {
            "orcid": "0000-0001-2345-6789",
            "openalex_url": "https://openalex.org/author/1234",
            "last_known_institution": "Test University",
            "num_of_works": 10,
            "num_of_citations": 100
        },
        "data": [
            {"topic": "Physics", "num_of_works": 5},
            {"topic": "Math", "num_of_works": 3}
        ]
    }

    # Fix: Patch get_author_ids and execute_query, not search_by_author.
    from unittest.mock import patch
    """ And when I patch, I depend on the underlying functions instead of high-level Application Programming Interface functions for accurate testing at a micro-leveling of the "alias", import patch.  """
    with patch("backend.app.get_author_ids", return_value=[{"author_id": "1234"}]):
        with patch("backend.app.execute_query", return_value=[(mock_result,)]):
            result = search_by_author("Test Author")

            # Validate schema structure
            assert "author_metadata" in result
            assert "data" in result

            # Validate author_metadata fields
            metadata = result["author_metadata"]
            assert "orcid" in metadata
            assert "openalex_url" in metadata
            assert "last_known_institution" in metadata
            assert "num_of_works" in metadata
            assert "num_of_citations" in metadata

            # Validate data items
            for item in result["data"]:
                assert "topic" in item
                assert "num_of_works" in item


def test_institution_search_result_schema():
    """
    Test that the institution search result follows the expected schema.
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

    from unittest.mock import patch
    with patch("backend.app.get_institution_id", return_value=123):
        with patch("backend.app.execute_query", return_value=[(mock_result,)]):
            result = search_by_institution("Test University")

            assert "institution_metadata" in result
            assert "data" in result

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
    Test that the topic search result follows the expected schema.
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
            {"institution_name": "State University", "num_of_authors": 100},
        ]
    }

    from unittest.mock import patch
    with patch("backend.app.execute_query", return_value=[(mock_result,)]):
        result = search_by_topic("Chemistry")

        assert "subfield_metadata" in result
        assert "totals" in result
        assert "data" in result

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
