# ============================================================
#  FreedomForge AI — core/logger.py
#  Logging — writes to logs/app.log, rotates at 1 MB
# ============================================================

import os
import logging
from logging.handlers import RotatingFileHandler
from utils.paths import LOGS_DIR as _LOGS_DIR

_LOG_DIR  = str(_LOGS_DIR)
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")

_logger: logging.Logger = None


def init() -> None:
    global _logger
    os.makedirs(_LOG_DIR, exist_ok=True)

    _logger = logging.getLogger("FreedomForgeAI")
    _logger.setLevel(logging.DEBUG)

    if _logger.handlers:
        return

    # File handler — rotates at 1 MB, keeps 3 backups
    fh = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _logger.addHandler(fh)

    # Console handler for development
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    _logger.addHandler(ch)


def _get() -> logging.Logger:
    if _logger is None:
        init()
    return _logger


def info(msg: str)      -> None: _get().info(msg)
def warning(msg: str)   -> None: _get().warning(msg)
def error(msg: str)     -> None: _get().error(msg)
def debug(msg: str)     -> None: _get().debug(msg)
def exception(msg: str) -> None: _get().exception(msg)
