"Separate service handlig timed out drives and jobs. Runs indepentend of the main files"
from time import sleep
import logging

import config
from resources import messages

logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
logger.addHandler(console_handler)

while True:
    for message in messages.get_all():
        if int(message.id) < messages.max_timestamp():
            messages.delete(message)
            logging.info("Deleted a message: id %s", message.id)
    sleep(5)
