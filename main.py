import os
import time
import logging
import ccxt
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env

api_key = os.getenv('BINANCE_API_KEY')
secret = os.getenv('BINANCE_SECRET_KEY')

if not api_key or not secret:
    raise Exception("API key and secret must be set in environment variables.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Exchange configuration with automatic time adjustment
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True
    }
})

# Trading parameters
symbol = 'BTC/USDT'
timeframe = '1d'
limit = 20


def fetch_data():
    """
    Fetch recent OHLCV data for the trading pair.
    Each bar format: [timestamp, open, high, low, close, volume]
    """
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return bars
    except ccxt.NetworkError as e:
        logging.error("Network error fetching data: %s", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error fetching data: %s", e)
    except Exception as e:
        logging.error("Unexpected error fetching data: %s", e)
    return None


def calculate_ma(prices, period):
    """
    Calculate the simple moving average (SMA) for a list of prices.
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_fibonacci_levels(high, low):
    """
    Given a high and low price, calculate common Fibonacci retracement levels.
    Levels are calculated using ratios: 23.6%, 38.2%, 50%, 61.8% along with 100%.
    """
    diff = high - low
    levels = {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }
    return levels


def main():
    position = None  # 'long', 'short', or None
    retry_delay = 60  # Initial retry delay in seconds

    while True:
        bars = fetch_data()
        if bars is None:
            logging.info("Retrying after %d seconds...", retry_delay)
            time.sleep(retry_delay)
            continue

        # Extract closing prices from the bars
        closes = [bar[4] for bar in bars]

        # Calculate moving averages (using 5 and 10 period examples)
        short_ma = calculate_ma(closes, period=5)
        long_ma = calculate_ma(closes, period=10)

        if short_ma is None or long_ma is None:
            logging.info("Not enough data to calculate moving averages. Waiting...")
            time.sleep(retry_delay)
            continue

        logging.info("Short MA (5): %.2f | Long MA (10): %.2f", short_ma, long_ma)

        # Calculate Fibonacci retracement levels using the highest high and lowest low
        highs = [bar[2] for bar in bars]  # high prices of each bar
        lows = [bar[3] for bar in bars]  # low prices of each bar

        # For simplicity, use the maximum high and minimum low in the fetched data
        recent_high = max(highs)
        recent_low = min(lows)
        fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
        logging.info("Fibonacci Levels: %s", fib_levels)

        # Example Strategy Combining MAs and Fibonacci:
        #
        # If the short MA crosses above the long MA (BUY signal)
        # AND current price is near a key Fibonacci support level (e.g., 61.8% level),
        # you might consider this a stronger signal to buy.
        #
        # Similarly, if short MA falls below long MA (SELL signal) and price is near a
        # Fibonacci resistance, this may strengthen your decision to sell.

        current_price = closes[-1]

        # Define a tolerance to check if the price is near a Fibonacci level (e.g., within 1%)
        tolerance = 0.01

        def near_fibonacci(target, price, tol):
            return abs(price - target) / target <= tol

        # Check if price is near the 61.8% level (commonly used as support)
        near_support = near_fibonacci(fib_levels['61.8%'], current_price, tolerance)

        if short_ma > long_ma and position != 'long':
            logging.info("Signal: BUY")
            if near_support:
                logging.info("Price %.2f is near the 61.8%% Fibonacci support at %.2f", current_price,
                             fib_levels['61.8%'])
            else:
                logging.info("Price %.2f is not near the preferred Fibonacci support.", current_price)
            # Uncomment below line to execute an actual order
            # order = exchange.create_market_buy_order(symbol, amount)
            position = 'long'
        elif short_ma < long_ma and position != 'short':
            logging.info("Signal: SELL")
            # Check if price is near a Fibonacci resistance, such as the 38.2% retracement level, or use your own logic.
            near_resistance = near_fibonacci(fib_levels['38.2%'], current_price, tolerance)
            if near_resistance:
                logging.info("Price %.2f is near the 38.2%% Fibonacci resistance at %.2f", current_price,
                             fib_levels['38.2%'])
            else:
                logging.info("Price %.2f is not near the preferred Fibonacci resistance.", current_price)
            # Uncomment below line to execute an actual order
            # order = exchange.create_market_sell_order(symbol, amount)
            position = 'short'
        else:
            logging.info("No new signal. Holding position: %s", position)

        # Wait for the next iteration
        time.sleep(60)


if __name__ == '__main__':
    try:
        main()
    finally:
        exchange.close()  # Ensure proper connection closing
