""" "Here" we have got the current plan for the backend testing logger setup. This means that we can check, if the logger is being configured and then log at least one messages that is, at the level of the INFO or even above!  """
import logging
import pytest
from backend.app import app, logger


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
    If you want to know, caplog.records is a list of LogRecord type of objects. This is just a test that is parameterized to confirm logs that have different log levels as well as "different" messages.
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
    Now, our Flask app microservices are ready to be tested with the logging of a specific message. Parameterizes the test for the Flask app logging with different levels as well as different messages.
    """
    with caplog.at_level(flask_log_level):
        app.logger.log(flask_log_level, flask_log_message)
    assert flask_log_message in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == flask_log_level
