"""
Logging configuration for the application
"""

import logging
import logging.config
from app.config import get_settings

settings = get_settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(filename)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        # "file": {
        #     "class": "logging.handlers.RotatingFileHandler",
        #     "level": settings.LOG_LEVEL,
        #     "formatter": "detailed",
        #     "filename": "/app/logs/app.log",
        #     "maxBytes": 10485760,  # 10MB
        #     "backupCount": 5,
        # },
    },
    "loggers": {
        "": {
            "handlers": ["console"],  # "file"],
            "level": settings.LOG_LEVEL,
            "propagate": True,
        },
        "uvicorn.access": {
            "handlers": ["console"],  # "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def setup_logging():
    """Configure logging for the application"""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    return logger


logger = setup_logging()
