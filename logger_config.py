# logger_config.py
import os
import logging

def setup_logging(log_file: str = "trading_bot.log"):
    os.makedirs("logs", exist_ok=True)

    # Reset handlers if already configured
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"logs/{log_file}")
        ]
    )
