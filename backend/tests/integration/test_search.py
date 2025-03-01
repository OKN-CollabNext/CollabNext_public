""" In the meantime, we can get started on importing some specific functions for searching that we "would like" to test and then we can import everything and alternately we can individually test.  """
from unittest.mock import patch
import pytest
from backend.app import (
    search_by_author,
    search_by_institution,
    search_by_topic,
)


@pytest.mark.integration
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
    Here we are going to make a parametric test for searching by the author, this is for the function named search_by_author with "different" database return scenarios.
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


@pytest.mark.integration
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
        assert (
            result["institution_metadata"]["institution_name"] == institution_name
        ), "Institution name mismatch"
    else:
        assert result is None


@pytest.mark.integration
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
                    {"institution_name": "State University",
                        "num_of_authors": 100},
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
    We originally did this parametric test for search_by_topic. We could of course make mock tests, but in this case, I want to be quite brief about what I am doing. I am doing a fixture that tests..that follow up on the patch `app.execute_query` regularly to make it so that yes, we can get more specifics on executing queries infrastructure-wise in order to prevent "actual" database calls from being made.
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
