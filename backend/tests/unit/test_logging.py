"""
Logging Tests

This file contains tests for the logging functionality of the application.
Tests include:
- Logger setup and configuration
- Log level handling
- Flask app logging integration
- Handler configuration
"""

import logging
import os
import pytest
from unittest.mock import patch, MagicMock
from backend.app import app, logger, setup_logger


@pytest.fixture
def mock_log_path():
    """
    Fixture to provide a consistent mock log path for tests.
    """
    with patch("backend.app.os.environ.get") as mock_env:
        mock_env.return_value = None
        yield "logs"


@pytest.mark.parametrize(
    "log_message, log_level",
    [
        ("This is a test log message", logging.INFO),
        ("Another test message", logging.WARNING),
    ],
    ids=["InfoLog", "WarningLog"]
)
def test_logger_setup(caplog, log_message, log_level):
    """
    Tests that our custom logger logs messages at expected levels.
    """
    with caplog.at_level(log_level):
        logger.log(log_level, log_message)
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelno == log_level
    assert log_message in caplog.text


@pytest.mark.parametrize(
    "flask_log_message, flask_log_level",
    [
        ("A Flask warning occurred", logging.WARNING),
        ("A Flask info occurred", logging.INFO),
    ],
    ids=["WarningCase", "InfoCase"]
)
def test_flask_app_logging(caplog, flask_log_message, flask_log_level):
    """
    Tests Flask's builtin logger messages at different levels.
    """
    with caplog.at_level(flask_log_level):
        app.logger.log(flask_log_level, flask_log_message)
    assert flask_log_message in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == flask_log_level


def test_setup_logger_has_all_handlers(mock_log_path):
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.os.makedirs") as mock_makedirs, \
            patch("backend.app.RotatingFileHandler") as mock_handler:

        mock_exists.return_value = False

        """ Each time RotatingFileHandler is called, return a new MagicMock()
        whose '.level' is set to something similar: an actual int """
        def _handler_side_effect(*args, **kwargs):
            """ And that's, the correct mock logging definitional function event-driven attributes, at the level of the log, for which we can handle all that appears as a side effect (all those paths paid off).  """
            handler_mock = MagicMock()
            handler_mock.level = logging.DEBUG  # or logging.NOTSET, etc.
            return handler_mock

        mock_handler.side_effect = _handler_side_effect

        test_logger = setup_logger()  # This calls RotatingFileHandler internally

        # Now you can do your checks safely without breaking logging
        mock_makedirs.assert_called_once_with(mock_log_path)
        assert mock_handler.call_count >= 5
        assert len(test_logger.handlers) >= 5

        handler_levels = [h.level for h in test_logger.handlers]
        assert logging.DEBUG in handler_levels
        assert logging.INFO in handler_levels
        assert logging.WARNING in handler_levels
        assert logging.ERROR in handler_levels
        assert logging.CRITICAL in handler_levels


# def test_setup_logger_azure_environment():
#     """
#     Test that setup_logger uses the correct log path in Azure environment.
#     """
#     with patch("backend.app.os.environ.get") as mock_env, \
#             patch("backend.app.os.path.exists") as mock_exists, \
#             patch("backend.app.os.makedirs") as mock_makedirs, \
#             patch("backend.app.RotatingFileHandler") as mock_handler:

#         # Setup Azure environment
#         mock_env.return_value = "some-azure-site"
#         mock_exists.return_value = True
#         mock_handler_instance = MagicMock()
#         mock_handler.return_value = mock_handler_instance

#         # Call the function under test
#         setup_logger()

#         # Verify Azure log path
#         mock_handler.assert_called()
#         call_args = mock_handler.call_args_list[0]
#         log_path = call_args[0][0]
#         assert "/home/LogFiles/" in log_path, "Should use Azure log path"
