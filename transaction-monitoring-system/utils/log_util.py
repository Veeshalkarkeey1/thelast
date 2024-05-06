import logging

# logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_handler = logging.StreamHandler()
log_formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s:%(message)s')
logger_handler.setFormatter(log_formatter)
logger.addHandler(logger_handler)