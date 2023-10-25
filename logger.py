# Start time of application
import time
import logging


start_time = time.time()


class RelativeTimeFormatter(logging.Formatter):
    def format(self, record):
        delta = time.time() - start_time
        record.relativeTime = round(delta * 1000, 2)  # milliseconds
        return super().format(record)


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = RelativeTimeFormatter("%(relativeTime)dms: %(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
