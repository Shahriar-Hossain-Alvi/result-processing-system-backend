import logging
from types import FrameType
from typing import Optional
from loguru import logger
import sys


class InterceptHandler(logging.Handler):
    """
    Send Standard Python logging messages to Loguru
    It will colorize the internal Log messages of SQLAlchemy and FastAPI
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame: Optional[FrameType] = logging.currentframe()
        depth: int = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        # Print message using Loguru
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage())


# call the setup_logging function at the top of the main.py (brfore app = FastAPI() call)
def setup_logging():
    # remove default loggers of Loguru
    logger.remove()

    # set new format for terminal
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    # Intercept pythons standard logging (eg: SQLAlchemy)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # For SQLAlchemy's Query (should use echo=False in engine creation)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

    return logger
