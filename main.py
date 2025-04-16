# main.py
import time
import logging
from typing import Optional, List, Tuple
from data import fetch_data, exchange
from strategy import calculate_fibonacci_levels, evaluate_signals
from logger_config import setup_logging
from config import SYMBOL, RETRY_DELAY, RESET_POSITION_TIMEOUT


def extract_prices(bars: List[List[float]]) -> Tuple[List[float], List[float], List[float]]:
    """
    Extract closing, high, and low prices from the fetched OHLCV bars.
    """
    closes = [bar[4] for bar in bars]
    highs = [bar[2] for bar in bars]
    lows = [bar[3] for bar in bars]
    return closes, highs, lows


def execute_trade(signal: str, position: Optional[str]) -> Optional[str]:
    """
    Execute a trade if the signal suggests a position change.
    Returns the new position or current one if no trade is made.
    """
    if signal == 'BUY' and position != 'long':
        logging.info("BUY signal received; executing BUY order.")
        # exchange.create_market_buy_order(SYMBOL, amount)
        return 'long'
    elif signal == 'SELL' and position != 'short':
        logging.info("SELL signal received; executing SELL order.")
        # exchange.create_market_sell_order(SYMBOL, amount)
        return 'short'
    else:
        logging.info("No trade action. Current position: %s", position)
        return position


def main():
    setup_logging()
    logging.info("Starting trading bot with symbol %s", SYMBOL)

    position: Optional[str] = None
    last_trade_time = time.time()

    while True:
        try:
            bars = fetch_data()
            if not bars:
                logging.warning("No data fetched. Retrying in %d seconds...", RETRY_DELAY)
                time.sleep(RETRY_DELAY)
                continue

            closes, highs, lows = extract_prices(bars)
            current_price = closes[-1]
            recent_high = max(highs)
            recent_low = min(lows)

            fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
            logging.info("Current price: %.2f | Fibonacci Levels: %s", current_price, fib_levels)

            signal = evaluate_signals(closes, fib_levels)
            logging.info("Trading Signal: %s", signal)

            new_position = execute_trade(signal, position)
            if new_position != position:
                position = new_position
                last_trade_time = time.time()

            if time.time() - last_trade_time > RESET_POSITION_TIMEOUT:
                logging.info("Reset timeout reached. Clearing position.")
                position = None
                last_trade_time = time.time()

        except Exception as e:
            logging.error("An error occurred in the main loop: %s", e, exc_info=True)

        time.sleep(RETRY_DELAY)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting trading bot...")
    finally:
        exchange.close()
        logging.info("Exchange connection closed.")
