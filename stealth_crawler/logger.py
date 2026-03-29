import logging
import os
from typing import Optional


def get_logger(name: str = "stealth_crawler", level: str = "INFO", log_file: Optional[str] = None):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    has_console = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in logger.handlers
    )
    if not has_console:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    if log_file:
        target_file = os.path.abspath(log_file)
        has_file = any(
            isinstance(handler, logging.FileHandler)
            and getattr(handler, "baseFilename", None) == target_file
            for handler in logger.handlers
        )
        if not has_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
