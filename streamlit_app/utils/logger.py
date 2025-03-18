import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configure file for the current session
log_file = log_dir / f"streamlit_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def setup_logging(level=None):
    """
    Set up logging configuration with both console and file handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
              If None, uses LOG_LEVEL from environment or defaults to INFO
    """
    if level is None:
        level_str = os.getenv("LOG_LEVEL", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Log initial message
    root_logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    root_logger.info(f"Log file: {log_file}")
    
    return root_logger

def get_logger(name):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)

def log_exception(logger, e, message="An error occurred"):
    """
    Log an exception with traceback information.
    
    Args:
        logger: Logger instance
        e: Exception object
        message: Custom message prefix
    """
    import traceback
    logger.error(f"{message}: {str(e)}")
    logger.debug("Exception traceback:", exc_info=True)
    return f"{message}: {str(e)}" 