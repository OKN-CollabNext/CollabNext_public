import pytest
from unittest.mock import patch
from backend.app import get_institution_id


@pytest.mark.integration
@pytest.mark.parametrize(
    "institution_name, expected_id",
    [
        ("Howard University", 1234),
        ("Spelman College", 5678),
        ("Hampton University", 9999),
    ],
    ids=["Howard", "Spelman", "Hampton"]
)
@patch("backend.app.execute_query")
def test_institution_id_lookup(mock_execute_query, institution_name, expected_id):
    # Here I am testing the lookup for the institution ID. I am returning one row with one column that "has" a dictionary: e.g. [({'institution_id': 4321},)]
    mock_execute_query.return_value = [({'institution_id': expected_id},)]
    db_id = get_institution_id(institution_name)
    assert db_id == expected_id, f"Expected {expected_id}, got {db_id}"

# ---------------------------------------------------------------------
# Let's do some incremental "one step at a time" testing.
# ---------------------------------------------------------------------


@pytest.mark.incremental
class TestUserLifecycle:
    def test_create_user(self):
        """ There is such a thing as a complete data science and machine learning lifecycle. In it we imagine that we are creating a user, logically progressing through the lifecycle of a user on the CollabNext-Alpha website or its successor called CollabNext_Public where we create a user. """
        user_created = True
        assert user_created

    def test_get_user(self):
        """ When we create a user, we automatically xfail it if the test_create_user fails. """
        got_user = True
        assert got_user
