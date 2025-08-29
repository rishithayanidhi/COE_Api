# app/core/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Logger configuration
logger = logging.getLogger("resource_hub_logger")
logger.setLevel(logging.INFO)

# File handler (rotates logs to avoid large files)
file_handler = RotatingFileHandler(f"{LOG_DIR}/app.log", maxBytes=5*1024*1024, backupCount=3)
file_handler.setLevel(logging.INFO)

# Console handler (for development)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Helper functions
def log_info(message: str):
    logger.info(message)

def log_warning(message: str):
    logger.warning(message)

def log_error(message: str):
    logger.error(message)
