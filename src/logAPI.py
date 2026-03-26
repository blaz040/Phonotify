import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOG_PATH = BASE_DIR / "logs" / "main.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Rotating file handler: max 50 KB, keep 1 backup
handler = RotatingFileHandler(
    LOG_PATH,
    maxBytes=50 * 1024,  # 50 KB
    backupCount=1         # keep one old log
)

#formatter = logging.Formatter("%(asctime)s - [ %(levelname)s ] - %(message)s")
#handler.setFormatter(formatter)
formatter = logging.Formatter("%(asctime)s - [ %(levelname)s ] - [%(tag)s] - %(message)s")
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

# Create logger
log = logging.getLogger("phonotify")
log.setLevel(logging.INFO)
log.addHandler(handler)

def init_log(tag: str = "Default") -> logging.LoggerAdapter:
    static_tag = {"tag": f"{tag}"}
    tmp_log = logging.LoggerAdapter(log, static_tag)
    return tmp_log 
