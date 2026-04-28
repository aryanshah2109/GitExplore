import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from backend.app.core.config_loader import config
from backend.app.core.path_constants import LOGS_PATH, MAX_LOG_SIZE

LOG_NAME = getattr(config.logging, "name", "gitexplore")


def get_logger():
    return logging.getLogger(LOG_NAME)


def configure_logger():
    try:
        # create logs directory
        LOGS_PATH.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(LOG_NAME)

        LOG_LEVEL = getattr(logging, config.logging.level.upper(), logging.INFO)
        LOG_FORMAT = logging.Formatter(config.logging.format)

        # set logger level
        logger.setLevel(LOG_LEVEL)

        # clear existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(LOG_FORMAT)

        # file handler
        log_file = LOGS_PATH / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=5
        )
        
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(LOG_FORMAT)

        # attach handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        logger.info("Logger configured successfully")

    except Exception as e:
        logging.error(f"Error while creating logger object: {e}")
        raise