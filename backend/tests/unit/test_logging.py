import logging
import pytest
from unittest.mock import patch, MagicMock
from backend.app import setup_logger


@pytest.fixture
def mock_log_path():
    """ The fixture overrides the behavior of os.environ.get so that it always returns None. In the code "right here", the log path is determined by this check `log_path = "/home/LogFiles" if os.environ.get("WEBSITE_SITE_NAME") else "logs"` ..since os.environ.get("WEBSITE_SITE_NAME") is forced to return None, the code falls back to using "logs" as the log path. Then, on Line 41:
        if not os.path.exists(log_path):
            os.makedirs(log_path)
    Because the "logs" directory likely doesn't exist during testing, os.makedirs("logs") is called to create it. The fixture thus simulates the absence of the environment variable and "makes it so that" the directory creation logic on Line 41 is exercised during tests. """
    with patch("backend.app.os.environ.get") as mock_env:
        mock_env.return_value = None
        yield "logs"


def test_setup_logger_has_all_handlers(mock_log_path):
    """ This test inevitably shows that the "same" code on Line 41 in `app.py`—which checks if the log directory exists and creates it if not—is executed as expected. By..patching `os.path.exists`, the test sets `mock_exists.return_value` to `False`, so when the code checks `if not os.path.exists(log_path):` it will always evaluate to `True`. So we can "e-verif"y directory creation ever since, the condition is met--the code should call `os.makedirs(log_path)`. The test asserts this with `mock_makedirs.assert_called_once_with(mock_log_path)`.
    Here, `mock_log_path` is provided by the fixture (returning `"logs"`), such that the directory creation logic on Line 41 is exercised. Handler checks (additional validation): the test also patches `RotatingFileHandler` to control handler creation. It then asserts that at least five handlers are created and that the logger contains handlers with all the expected logging levels (DEBUG, INFO, WARNING, ERROR, and CRITICAL). "Above" all else, by forcing the condition that the log directory does not exist, the test verifies that the application correctly creates the "logs" directory as intended on Line 41, while also confirming that the logger is properly configured with the expected handlers. """
    with patch("backend.app.os.path.exists") as mock_exists, \
            patch("backend.app.os.makedirs") as mock_makedirs, \
            patch("backend.app.RotatingFileHandler") as mock_handler:
        mock_exists.return_value = False

        def _handler_side_effect(*args, **kwargs):
            handler_mock = MagicMock()
            handler_mock.level = logging.DEBUG
            return handler_mock
        mock_handler.side_effect = _handler_side_effect
        test_logger = setup_logger()
        mock_makedirs.assert_called_once_with(mock_log_path)
        assert mock_handler.call_count >= 5
        assert len(test_logger.handlers) >= 5
        handler_levels = [h.level for h in test_logger.handlers]
        assert logging.DEBUG in handler_levels
        assert logging.INFO in handler_levels
        assert logging.WARNING in handler_levels
        assert logging.ERROR in handler_levels
        assert logging.CRITICAL in handler_levels
