import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.core.config import settings


def setup_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL.upper())
    logger.addHandler(console_handler)

    if settings.LOG_FILE:
        try:
            log_path = Path(settings.LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                filename=str(log_path),
                maxBytes=10485760,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(settings.LOG_LEVEL.upper())
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to setup to logger.. {str(e)} ")
    logger.propagate = False
    return logger


logger = setup_logger()
