"""
Logging configuration
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(config):
    """
    Setup application logger

    Args:
        config: Application configuration

    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger('sonarr-extension-filter')
    logger.setLevel(getattr(logging, config.logging.level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if config.logging.console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if config.logging.file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(config.logging.file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            config.logging.file,
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
