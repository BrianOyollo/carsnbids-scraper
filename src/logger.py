import logging
from pythonjsonlogger.json import JsonFormatter

def setup_json_logger(log_file="logs.json"):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # clear existing handlers
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    formatter = JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger
