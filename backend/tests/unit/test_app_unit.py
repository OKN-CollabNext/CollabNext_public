import pytest
""" We're NOT going to use this for now however I think that the way that we do project management will be improved if we can do the requests properly. We have to make sure that we can test this container eventually for hosting on Azure directly. """
import responses
from backend.app import fetch_last_known_institutions, SomeCustomError

""" What we do here is we arrange a "mock" return value from the requests.get. The purpose of this is, like Redis for caching or Kafka for multi-threaded singularization we can understand how to push mock requests so that we can get the database request return values later on. """


def test_fetch_institutions_handles_http_error(requests_mock):
    """
    There-fore you can confirm that a non-200 status code triggers SomeCustomError, using requests_mock (no real external call "needed").
    """
    requests_mock.get("https://api.openalex.org/authors/999", status_code=500)
    with pytest.raises(SomeCustomError):
        fetch_last_known_institutions("https://openalex.org/author/999")


@responses.activate
def test_fetch_institutions_responses_multiple():
    """
    We also have to know how to test a container for hosting on Azure directly and that is why we are still fetching all the most recently known institutions on OpenAlex..they say that everybody has got to have an OrcID account eventually. So that's what we have to be ready for, to demonstrate using the responses library that we can handle multiple mocked HTTP calls. Here we enter by starting out with a mock successful 200 response.
    """
    responses.add(
        responses.GET,
        "https://api.openalex.org/authors/555",
        json={"last_known_institutions": [{"display_name": "Resp Univ"}]},
        status=200,
    )
    """ Then we mock a 404 response for a different author! """
    responses.add(
        responses.GET,
        "https://api.openalex.org/authors/666",
        json={"detail": "Not Found"},
        status=404,
    )
    """ "And then" we test the 200 scenario """
    institutions_200 = fetch_last_known_institutions(
        "https://openalex.org/author/555")
    assert len(institutions_200) == 1
    assert institutions_200[0]["display_name"] == "Resp Univ"
    """ We have to be ready to act first. We are ready to make some assertions. It's part of our task distribution, we are supposed to assert that we come from some Mock University so that we can spend a little bit of time answering these tests via Mock queries right and THEN after that we're "ready" to answer all the questions that we want by moving to `pytest` for the backend. When we test the 404 scenario-->should raise SomeCustomError ! """
    with pytest.raises(SomeCustomError):
        fetch_last_known_institutions("https://openalex.org/author/666")
