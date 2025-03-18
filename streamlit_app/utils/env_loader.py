import os
from pathlib import Path
from dotenv import load_dotenv
from .logger import get_logger

logger = get_logger(__name__)

def load_env_file():
    """
    Load environment variables from .env file in the project root.
    
    Returns:
        dict: Dictionary of environment variables loaded from .env file
    """
    # Find the project root directory (where .env file should be)
    current_dir = Path(__file__).parent.parent.parent
    env_path = current_dir / ".env"
    
    # Check if .env file exists
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using default environment variables.")
        return {}
    
    # Load the .env file
    logger.info(f"Loading environment variables from {env_path}")
    load_dotenv(dotenv_path=env_path)
    
    # Read relevant environment variables
    env_vars = {
        "CLIENT_ID": os.getenv("CLIENT_ID", ""),
        "CLIENT_SECRET": os.getenv("CLIENT_SECRET", ""),
        "RH_BASE_URL": os.getenv("RH_BASE_URL", ""),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "CACHE_ENABLED": os.getenv("CACHE_ENABLED", "true").lower() == "true",
        "RATE_LIMIT_DELAY": float(os.getenv("RATE_LIMIT_DELAY", "0"))
    }
    
    # Log loaded variables (but mask sensitive information)
    logger.info("Environment variables loaded:")
    logger.info(f"  CLIENT_ID: {'*' * 8 if env_vars['CLIENT_ID'] else 'Not set'}")
    logger.info(f"  CLIENT_SECRET: {'*' * 8 if env_vars['CLIENT_SECRET'] else 'Not set'}")
    logger.info(f"  RH_BASE_URL: {env_vars['RH_BASE_URL'] if env_vars['RH_BASE_URL'] else 'Not set'}")
    logger.info(f"  LOG_LEVEL: {env_vars['LOG_LEVEL']}")
    logger.info(f"  CACHE_ENABLED: {env_vars['CACHE_ENABLED']}")
    logger.info(f"  RATE_LIMIT_DELAY: {env_vars['RATE_LIMIT_DELAY']}")
    
    return env_vars 