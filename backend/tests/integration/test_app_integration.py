""" Now it is time to "switch gears" to testing the app in integration testing on local. The version of this is such that we can test things via `pytest` which includes something called a fixture which means that we can initialize a Flask client "for the sole purpose of" testing. """
import pytest
from unittest.mock import patch
from backend.app import app, fetch_last_known_institutions, SomeCustomError


@pytest.mark.integration
@pytest.mark.parametrize(
    "openalex_url, mock_response, expected_length, expected_display_name",
    [
        (
            "https://openalex.org/author/1234",
            {
                "last_known_institutions": [
                    {"display_name": "Mock University",
                        "id": "https://openalex.org/mockInstitutionId"}
                ]
            },
            1,
            "Mock University"
        ),
        (
            "https://openalex.org/author/9999",
            {
                "last_known_institutions": [
                    {"display_name": "Another Univ",
                        "id": "https://openalex.org/anotherId"},
                    {"display_name": "Second Univ",
                        "id": "https://openalex.org/secondId"}
                ]
            },
            2,
            "Another Univ"
        ),
    ],
    ids=["SingleInstitution", "MultipleInstitutions"]
)
@patch("backend.app.requests.get")
def test_fetch_last_known_institutions(
    mock_get,
    openalex_url,
    mock_response,
    expected_length,
    expected_display_name
):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    results = fetch_last_known_institutions(openalex_url)
    assert len(results) == expected_length
    assert results[0]["display_name"] == expected_display_name


@pytest.fixture
def client():
    """If all is okay then we can do the creation of a Flask test client for the app..this is just an example and in fact it assumes that we have checked via the test initial search ok function that the initial search returns a status of 200 when given valid input. """
    with app.test_client() as client:
        yield client


@pytest.mark.integration
@pytest.mark.parametrize(
    "post_json, expected_status",
    [
        (
            {
                "organization": "Howard University",
                "researcher": "Chinar Dean Aastika",
                "topic": "Chemistry",
                "type": "HBCU"
            },
            200,
        ),
        (
            {
                "organization": "NoSuch Institution",
                "researcher": "No One",
                "topic": "Astrophysics",
                "type": "HBCU"
            },
            200,
        ),
    ],
    ids=["ValidSearch", "UnknownInstitution"]
)
def test_initial_search_ok(client, post_json, expected_status):
    """
    Now here's the tricky part; if we have this backend testing framework, then we have to make sure that we expect a certain type of format in the response JavaScript Object Notation Orientation..that's the response that we have gotten when we do the integration test for the /initial-search endpoint with different JavaScript Object Notation payloads here.
    """
    response = client.post("/initial-search", json=post_json)
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}"
    )
    data = response.get_json()
    """ As we need for example, maybe you expect the key of "graph" that is if the data was found..otherwise we're going to want to assert the "graph" in the data. We can perform additional checks if we need, however this is "sufficient for our purposes". """
