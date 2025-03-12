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
    """
    Check that setup_logger() attaches at least 5 handlers:
      DEBUG, INFO, WARNING, ERROR, CRITICAL.
    """
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.os.makedirs") as mock_makedirs, \
            patch("backend.app.RotatingFileHandler") as mock_handler:
        
        # Setup mocks
        mock_exists.return_value = False
        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance
        
        # Call the function under test
        test_logger = setup_logger()
        
        # Verify directory creation
        mock_makedirs.assert_called_once_with(mock_log_path)
        
        # Verify handler creation and configuration
        assert mock_handler.call_count >= 5, "Should create at least 5 handlers"
        assert len(test_logger.handlers) >= 5, "Expected at least five handlers."
        
        # Verify log levels
        handler_levels = [handler.level for handler in test_logger.handlers]
        assert logging.DEBUG in handler_levels, "No DEBUG handler found."
        assert logging.INFO in handler_levels, "No INFO handler found."
        assert logging.WARNING in handler_levels, "No WARNING handler found."
        assert logging.ERROR in handler_levels, "No ERROR handler found."
        assert logging.CRITICAL in handler_levels, "No CRITICAL handler found."


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