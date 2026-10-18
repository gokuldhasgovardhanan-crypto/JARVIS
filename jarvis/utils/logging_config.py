import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Privacy redaction patterns for API keys, tokens, etc.
SENSITIVE_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9_-]{20,})", re.IGNORECASE),
    re.compile(r"(Bearer\s+[a-zA-Z0-9_\-\.]{20,})", re.IGNORECASE),
    re.compile(r"(key[=:]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", re.IGNORECASE),
    re.compile(r"(api[_-]?key[=:]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", re.IGNORECASE),
]


class PrivacyFilter(logging.Filter):
    """Redacts API keys and sensitive tokens from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in SENSITIVE_PATTERNS:
                msg = pattern.sub("[REDACTED_SECRET]", msg)
            record.msg = msg
        return True


def setup_logger(
    name: str = "jarvis",
    log_dir: Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configures and returns a centralized, privacy-aware logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    privacy_filter = PrivacyFilter()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(privacy_filter)
    logger.addHandler(console_handler)

    # File handler
    if log_dir is None:
        log_dir = Path.home() / "AppData" / "Local" / "PersonalJarvis" / "logs"
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "jarvis.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(privacy_filter)
        logger.addHandler(file_handler)
    except Exception as exc:
        logger.warning(f"Failed to initialize rotating file log handler: {exc}")

    return logger


logger = setup_logger()
