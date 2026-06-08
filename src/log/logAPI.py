import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
LOG_PATH = BASE_DIR / "logs" / "main.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Handlers
file_handler = RotatingFileHandler(
    LOG_PATH,
    maxBytes=1 * 1024 * 1024,  # 1 KB
    backupCount=3         # keep one old log
)
console_handler = logging.StreamHandler(sys.stdout)

#Formatter
formatter = logging.Formatter("%(asctime)s - [ %(levelname)s ] - [%(tag)s] - %(message)s")

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Create logger
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(file_handler)
log.addHandler(console_handler)

def init_log(tag: str = "Default") -> logging.LoggerAdapter:
    static_tag = {"tag": f"{tag}"}
    tmp_log = logging.LoggerAdapter(log, static_tag)
    return tmp_log 
