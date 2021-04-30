import logging
import sys
from datetime import datetime
from logging import FileHandler

logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')


class Logger:
    logger = logging.getLogger("cdc-logger")
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logFormatter)
    logger.addHandler(ch)

    fh = FileHandler(
        f"/var/log/cdc_lesson_tracker/cdc_lesson_tracker_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.log")
    fh.setFormatter(logFormatter)
    logger.addHandler(fh)
