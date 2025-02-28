import logging
import pytest
from backend.app import app, logger


def test_logger_setup(caplog):
    """
    "Here" we have got is current plan for the backend testing logger set-up which means that we check, if the logger is being configured and we log at least one message that is at the level of the INFO or even above!
    """
    with caplog.at_level(logging.INFO):
        logger.info("This is a test log message")

    # caplog.records is a list of LogRecord objects
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.INFO
    assert "test log message" in caplog.text


def test_flask_app_logging(caplog):
    """
    Now, our Flask app microservices are ready to be tested with the logging of a specific message.
    """
    with caplog.at_level(logging.WARNING):
        app.logger.warning("A Flask warning occurred")

    assert "A Flask warning occurred" in caplog.text
    assert len(caplog.records) == 1
