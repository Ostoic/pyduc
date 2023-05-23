import functools
import logging
from dataclasses import asdict, dataclass
from logging.config import dictConfig

ROOT_LOGGER_NAME = "detector_server"


@dataclass(frozen=True, eq=True, slots=True)
class LogConfig:
    LOGGER_NAME = ROOT_LOGGER_NAME
    LOG_FORMAT = "%(levelprefix)s | %(name)s \t| %(asctime)s | %(message)s"
    LOG_LEVEL = logging.DEBUG

    version = 1
    disable_existing_loggers = False

    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }

    loggers = {LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL}}


def _config_logging():
    log_config = {
        "version": 1,
        "root": {"handlers": ["console"], "level": "DEBUG"},
        "handlers": {
            "console": {"formatter": "std_out", "class": "logging.StreamHandler", "level": "DEBUG"}
        },
        "formatters": {
            "std_out": {
                "format": "%(asctime)s |  %(levelname)s |  %(module)s |  %(funcName)s: %(message)s",
                "datefmt": "%d-%m-%Y %I:%M:%S",
            }
        },
    }

    dictConfig(log_config)


@functools.cache
def get_child_logger(name: str):
    full_name = name if name == ROOT_LOGGER_NAME else f"{ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(full_name)


_config_logging()
