import pytest
# We're NOT going to use this for now however I think that the way that we do project management will be improved if we can do the requests properly. We have to make sure that we can test this container eventually for hosting on Azure directly.
import requests
from unittest.mock import patch
from backend.app import app, fetch_last_known_institutions


@patch("backend.app.requests.get")
def test_fetch_last_known_institutions(mock_get):
    # What we do here is we arrange a "mock" return value from the requests.get. The purpose of this is, like Redis for caching or Kafka for multi-threaded singularization we can understand how to push mock requests so that we can get the database request return values later on.
    mock_get.return_value.json.return_value = {
        "last_known_institutions": [
            {"display_name": "Mock University",
                "id": "https://openalex.org/mockInstitutionId"}
        ]
    }
    # We also have to know how to test a container for hosting on Azure directly and taht's why we're still fetching all the last known institutions on OpenAlex..they say that everybody has got to have an account eventually. So that's what we do, we have to be ready to act first.
    results = fetch_last_known_institutions("https://openalex.org/author/1234")
    # Then we are ready to make some assertions. It's part of our task distribution, we are supposed to assert that we come from some Mock University so that we can spend a little bit of time answering these tests via Mock queries right and THEN after that we're "ready" to answer all the questions that we want by moving to pytest for the backend.
    assert len(results) == 1
    assert results[0]["display_name"] == "Mock University"


@pytest.fixture
def client():
    """
    Now it is time to "switch gears" to testing the app in local. The version of this is that we can test things via `pytest` which includes something called a fixture which means that we can initilize a Flask client for testing.
    """
    with app.test_client() as client:
        yield client


def test_initial_search_ok(client):
    """
    If all is okay then we can do the initial search..this is just an example and in fact it checks if /initial-search returns a status of 200 when given valid input.
    """
    response = client.post(
        "/initial-search",
        json={
            "organization": "Howard University",
            "researcher": "Chinar Dean Aastika",
            "topic": "Chemistry",
            "type": "HBCU"
        },
    )
    assert response.status_code == 200, "Should return 200 OK"
    # Now here's the tricky part if we have this backend testing framework we have to make sure that we expect a certain type of format in the response JavaScript Object Orientation Notation..that's the response that we get when we test it here.
    data = response.get_json()
    # For example, maybe you expect the key of "graph" that is if the data was
    # found..otherwise we're going to want to assert the "graph" in the data.
