import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Create logger
logger = logging.getLogger("excursionbot")
logger.setLevel(logging.INFO)

# Only add handlers if none exist yet - prevents duplicate logging
if not logger.handlers:
    # File handler
    log_filename = f"logs/excursionbot_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    logger.propagate = False 

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def log_query(user_message: str, response: str, sources: list, tokens: int):
    """Log a user query and response."""
    logger.info(
        f"QUERY | "
        f"message='{user_message[:100]}' | "
        f"sources={sources} | "
        f"tokens={tokens} | "
        f"response_length={len(response)}"
    )


def log_tool_call(tool_name: str, inputs: dict, success: bool):
    """Log a tool call."""
    logger.info(
        f"TOOL | "
        f"tool={tool_name} | "
        f"inputs={inputs} | "
        f"success={success}"
    )


def log_error(error: str, context: str = ""):
    """Log an error."""
    logger.error(
        f"ERROR | "
        f"context='{context}' | "
        f"error='{error}'"
    )


def log_session_start():
    """Log when a new session starts."""
    logger.info("SESSION_START | New user session started")


def log_session_end(total_messages: int, total_tokens: int):
    """Log when a session ends."""
    logger.info(
        f"SESSION_END | "
        f"total_messages={total_messages} | "
        f"total_tokens={total_tokens}"
    )