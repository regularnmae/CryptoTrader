import time
import logging
from typing import Optional, List, Tuple

from data import fetch_data, exchange
from strategy import calculate_fibonacci_levels, evaluate_signals
from logger_config import setup_logging
from config import SYMBOL, RETRY_DELAY, RESET_POSITION_TIMEOUT, MAX_RETRIES


class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class TradingBot:
    def __init__(
        self,
        symbol: str = SYMBOL,
        retry_delay: int = RETRY_DELAY,
        reset_timeout: int = RESET_POSITION_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ):
        self.symbol = symbol
        self.retry_delay = retry_delay
        self.reset_timeout = reset_timeout
        self.max_retries = max_retries

        self.position: Optional[str] = None
        self.last_trade_time = time.time()

        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def extract_prices(bars: List[List[float]]) -> Tuple[List[float], List[float], List[float]]:
        closes = [bar[4] for bar in bars]
        highs = [bar[2] for bar in bars]
        lows = [bar[3] for bar in bars]
        return closes, highs, lows

    def fetch_with_retry(self) -> Optional[List[List[float]]]:
        for attempt in range(1, self.max_retries + 1):
            try:
                bars = fetch_data()
                if bars:
                    return bars
                self.logger.warning("Empty data returned (attempt %d/%d)", attempt, self.max_retries)
            except DataFetchError as e:
                self.logger.warning("Fetch error on attempt %d/%d: %s", attempt, self.max_retries, str(e))
            time.sleep(self.retry_delay * attempt)

        self.logger.error("Failed to fetch data after %d attempts", self.max_retries)
        return None

    def execute_trade(self, signal: str) -> None:
        if signal == 'BUY' and self.position != 'long':
            self.logger.info("Executing BUY for %s", self.symbol)
            # exchange.create_market_buy_order(self.symbol, amount)
            self._update_position('long')

        elif signal == 'SELL' and self.position != 'short':
            self.logger.info("Executing SELL for %s", self.symbol)
            # exchange.create_market_sell_order(self.symbol, amount)
            self._update_position('short')

        else:
            self.logger.debug("No trade executed | Current: %s | Signal: %s", self.position, signal)

    def _update_position(self, new_position: str):
        self.position = new_position
        self.last_trade_time = time.time()
        self.logger.info("Position updated to %s", self.position)

    def reset_position_if_stale(self):
        if time.time() - self.last_trade_time > self.reset_timeout:
            self.logger.info("Resetting stale position (%ds timeout)", self.reset_timeout)
            self.position = None
            self.last_trade_time = time.time()

    def run(self):
        self.logger.info("Bot running on %s", self.symbol)
        while True:
            bars = self.fetch_with_retry()
            if not bars:
                time.sleep(self.retry_delay)
                continue

            closes, highs, lows = self.extract_prices(bars)
            if len(closes) < 20:
                self.logger.warning("Insufficient data for analysis. Waiting...")
                time.sleep(self.retry_delay)
                continue

            current_price = closes[-1]
            recent_high = max(highs[-20:])
            recent_low = min(lows[-20:])

            fib_levels = calculate_fibonacci_levels(recent_high, recent_low)
            signal = evaluate_signals(closes, fib_levels)

            self.logger.info("Price: %.2f | Signal: %s", current_price, signal)
            self.logger.debug("Fibonacci levels: %s", fib_levels)

            self.execute_trade(signal)
            self.reset_position_if_stale()

            time.sleep(self.retry_delay)


if __name__ == '__main__':
    setup_logging()
    logging.info("Launching TradingBot...")

    bot = TradingBot()

    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received. Shutting down gracefully...")
    finally:
        exchange.close()
        logging.info("Exchange connection closed.")
