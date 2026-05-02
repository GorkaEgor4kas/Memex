'''Logger setup'''
import sys
from pathlib import Path
from loguru import logger

def setup_logger(log_level: str = "INFO"):
    '''Configure loguru logger'''
    try:
        from core.config import config
        if hasattr(config, 'log_level'):
            log_level = config._log_level
    except ImportError:
        pass

    logger.remove()

    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    #file records
    log_path = Path.home() / ".obsidian-rag" / "app.log"
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    
