import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

# Load secrets
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')

# Raise error if missing
if not API_KEY:
    raise EnvironmentError("Missing BINANCE_API_KEY in .env")
if not SECRET_KEY:
    raise EnvironmentError("Missing BINANCE_SECRET_KEY in .env")

# Trading configuration
SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
TIMEFRAME = os.getenv('TIMEFRAME', '1m')
LIMIT = int(os.getenv('LIMIT', 20))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 60))  # seconds
RESET_POSITION_TIMEOUT = int(os.getenv('RESET_POSITION_TIMEOUT', 3600))  # seconds
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

# Optional: logging initial config
logging.info(f"Loaded config: {SYMBOL=} {TIMEFRAME=} {LIMIT=} {RETRY_DELAY=} {RESET_POSITION_TIMEOUT=}")
