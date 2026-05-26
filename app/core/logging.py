import logging
import sys
from app.core.config import settings

def setup_logging():
    # Define log format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    
    # Set log level based on DEBUG setting
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create application specific logger
    logger = logging.getLogger("app")
    logger.setLevel(level)
    
    # Silence overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("presidio-analyzer").setLevel(logging.INFO)
    
    logger.info(f"Logging initialized with level: {logging.getLevelName(level)}")
    return logger

logger = setup_logging()
