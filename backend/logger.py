import os
import logging
from logging.handlers import RotatingFileHandler

"""
This file has necessary methods to set up the logger for debugging.
"""

def setup_logger():
    """Configure logging with rotating file handler for all levels"""
    # Create logs directory if it doesn't exist
    log_path = "/home/LogFiles" if os.environ.get("WEBSITE_SITE_NAME") else "logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # Configure logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create handlers for different log levels with different storage allocations
    handlers = {
        "debug": RotatingFileHandler(
            os.path.join(log_path, "debug.log"),
            maxBytes=15*1024*1024,  # 10MB
            backupCount=3
        ),
        "info": RotatingFileHandler(
            os.path.join(log_path, "info.log"),
            maxBytes=15*1024*1024,  # 10MB
            backupCount=3
        ),
        "warning": RotatingFileHandler(
            os.path.join(log_path, "warning.log"),
            maxBytes=10*1024*1024,   # 5MB
            backupCount=3
        ),
        "error": RotatingFileHandler(
            os.path.join(log_path, "error.log"),
            maxBytes=5*1024*1024,   # 2MB
            backupCount=3
        ),
        "critical": RotatingFileHandler(
            os.path.join(log_path, "critical.log"),
            maxBytes=2*1024*1024,   # 1MB
            backupCount=3
        )
    }

    # Set levels and formatters for handlers
    handlers["debug"].setLevel(logging.DEBUG)
    handlers["info"].setLevel(logging.INFO)
    handlers["warning"].setLevel(logging.WARNING)
    handlers["error"].setLevel(logging.ERROR)
    handlers["critical"].setLevel(logging.CRITICAL)

    for handler in handlers.values():
        handler.setFormatter(formatter)

    # Get Flask's logger
    logger = logging.getLogger("flask.app")
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Add handlers to logger
    for handler in handlers.values():
        logger.addHandler(handler)

    return logger