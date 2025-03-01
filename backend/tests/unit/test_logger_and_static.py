"""
If you were to take a minimal example you would see that our unit tests are pretty minimal. That being "said", we know that our unit tests "verify" that:
1. the setup_logger() correctly creates & attaches all the handlers expected.
2. The static file serving route properly returns a file's content when it does exist, and falls back to returning index.html when the requested file is missing.
"""

import os
import pytest
from unittest.mock import patch
from backend.app import setup_logger, app


def test_setup_logger_has_all_handlers(tmp_path):
    """
    Test that the setup_logger() does create a logs directory that ..if that is needed that is and attaches the handlers for DEBUG & INFO & WARNING & ERROR & CRITICAL levels..they're levels.
    """
    logs_dir = tmp_path / "logs"
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.os.makedirs") as mock_makedirs:
        mock_exists.return_value = False
        logger = setup_logger()
        mock_makedirs.assert_called_once()
        assert len(
            logger.handlers) >= 5, "Expected at least five handlers to be attached."
        handler_levels = [handler.level for handler in logger.handlers]
        assert any(
            level == 10 for level in handler_levels), "No DEBUG handler found."
        assert any(
            level == 20 for level in handler_levels), "No INFO handler found."
        assert any(
            level == 30 for level in handler_levels), "No WARNING handler found."
        assert any(
            level == 40 for level in handler_levels), "No ERROR handler found."
        assert any(
            level == 50 for level in handler_levels), "No CRITICAL handler found."


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_static_file_serving_file_exists(client):
    """
    When you set up a static local server, you will know that the file has to exist and when a file exists in the "static" folder the route serves that file. We simulate file existence and a dummy response type from send_from_directory.
    """
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.send_from_directory") as mock_send:
        """ My suspicioun is that the existence of the file is database related and it is something that we have to simulate. When we simulate a file we don't "even" use the same file type we don't even have a file. This is important because "some testing libraries' are "literally" incompatible with especially "graphics files". So we simulate the existence of the file, because that makes everything else possible. """
        mock_exists.return_value = True
        """ Then, we can let the send_from_directory return some dummy file content. """
        mock_send.return_value = "file content"
        """ Upon which we request a file e.g. "/existing.txt")..and when we do, we do it. """
        response = client.get("/existing.txt")
        response_text = response.data.decode()
        assert response_text == "file content", "Expected the file content to be served."
        """ And we do, check that send_from_directory was called with the file requested. Existing techniques for accessing and sending and patching and deleting from the direcotry typically use static (current) sensor measurements to perform machine learning tasks, and in our case we want to check that we did call the send_from_directory with the file that we are learning and looking for. """
        static_folder = app.static_folder
        mock_send.assert_called_with(static_folder, "existing.txt")


def test_static_file_serving_file_not_exists(client):
    """
    Test that when a file doesn't exist then, the route falls back to serving index.html. "Even" if the file doesn't exist then we are able to get the index content visualized without the app's file necessarily needing to exist.
    """
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.send_from_directory") as mock_send:
        """ Therefore, I simulate that the requested file does NOT exist. """
        mock_exists.return_value = False
        """ I let send_from_directory return some dummy index content. """
        mock_send.return_value = "index content"
        """ We sprinkle that on and that makes us want more so we request a non-existent file e.g. "/nonexistent.txt". This is perfect for our unit tests "actually" because what we're doing is we're simulating files that don't exist in practicality but that are practically useful in terms of "saving data space".  """
        response = client.get("/nonexistent.txt")
        response_text = response.data.decode()
        assert response_text == "index content", "Expected fallback index.html content."
        static_folder = app.static_folder
        mock_send.assert_called_with(static_folder, "index.html")
