import ccxt
import logging
from typing import List, Optional, Any
from config import API_KEY, SECRET_KEY, SYMBOL, TIMEFRAME, LIMIT

# Create and configure the exchange instance
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True
    }
})

def fetch_data() -> Optional[List[List[Any]]]:
    """
    Fetch recent OHLCV data for the trading pair.
    Each bar format: [timestamp, open, high, low, close, volume]
    """
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=LIMIT)
        logging.debug("Fetched %d OHLCV bars for %s", len(bars), SYMBOL)
        return bars
    except ccxt.NetworkError as e:
        logging.error("Network error fetching data: %s", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error fetching data: %s", e)
    except Exception as e:
        logging.error("Unexpected error fetching data: %s", e)
    return None
