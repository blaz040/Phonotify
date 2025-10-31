import logging
logPath:str="myLogs.log"
logging.basicConfig(
    filename=logPath,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging

