import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOG_PATH = BASE_DIR / "logs" / "main.log"

# Create logger
log = logging.getLogger("phonotify")
log.setLevel(logging.INFO)

# Rotating file handler: max 50 KB, keep 1 backup
handler = RotatingFileHandler(
    LOG_PATH,
    maxBytes=50 * 1024,  # 50 KB
    backupCount=1         # keep one old log
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
handler.setLevel
log.addHandler(handler)

# Example usage
log.info("Logger initialized")

