import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env

# Load secrets
API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')

if not API_KEY:
    raise EnvironmentError("Missing BINANCE_API_KEY in .env")
if not SECRET_KEY:
    raise EnvironmentError("Missing BINANCE_SECRET_KEY in .env")

# Load trading config with fallbacks
SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
TIMEFRAME = os.getenv('TIMEFRAME', '5m')
LIMIT = int(os.getenv('LIMIT', 20))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 60))  # seconds
RESET_POSITION_TIMEOUT = int(os.getenv('RESET_POSITION_TIMEOUT', 3600))  # seconds

logging.info(f"Trading Config - SYMBOL: {SYMBOL}, TIMEFRAME: {TIMEFRAME}, LIMIT: {LIMIT}, RETRY_DELAY: {RETRY_DELAY}, RESET_TIMEOUT: {RESET_POSITION_TIMEOUT}")
