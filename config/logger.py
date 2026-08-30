"""
Centralized logging configuration.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from config.settings import settings

def setup_logger(name: str = "aarohan") -> logging.Logger:
    """Set up and return a logger with console and file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:  # avoid duplicate handlers
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(
        settings.LOG_DIR / "aarohan.log",
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger

# Default logger
logger = setup_logger()