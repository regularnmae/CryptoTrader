import time
import logging
import random
import signal
from typing import Optional, List, Tuple

from data import fetch_data, exchange
from ccxt.base.errors import BaseError as ExchangeError
from strategy import calculate_fibonacci_levels, evaluate_signals
from logger_config import setup_logging
from config import SYMBOL, RETRY_DELAY, RESET_POSITION_TIMEOUT, MAX_RETRIES


class TradingBot:
    """
    A signal-driven trading bot that handles minimum order size and precision.
    """
    def __init__(
        self,
        symbol: str = SYMBOL,
        retry_delay: int = RETRY_DELAY,
        reset_timeout: int = RESET_POSITION_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        trade_fraction: float = 0.1,
    ):
        self.symbol = symbol
        self.retry_delay = retry_delay
        self.reset_timeout = reset_timeout
        self.max_retries = max_retries
        self.trade_fraction = trade_fraction

        self.position: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.position_size: Optional[float] = None
        self.last_trade_time = time.time()
        self.running = False

        self.logger = logging.getLogger(self.__class__.__name__)
        # fetch market info for precision and limits
        markets = exchange.load_markets()
        market = exchange.markets.get(self.symbol, {})
        self.amount_precision = market.get('precision', {}).get('amount', 8)
        self.min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)

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
                self.logger.warning("Empty data (attempt %d/%d)", attempt, self.max_retries)
            except ExchangeError as e:
                self.logger.warning("Exchange error (attempt %d/%d): %s", attempt, self.max_retries, e)
            except Exception as e:
                self.logger.warning("Unexpected fetch error (attempt %d/%d): %s", attempt, self.max_retries, e)
            backoff = self.retry_delay * (2 ** (attempt - 1))
            sleep_time = backoff + random.uniform(0, self.retry_delay)
            time.sleep(sleep_time)
        self.logger.error("Max fetch attempts reached (%d). Skipping cycle.", self.max_retries)
        return None

    def open_position(self, price: float) -> None:
        """Open a position ensuring amount meets exchange minimum and precision."""
        # Calculate raw amount
        free_balance = exchange.fetch_balance().get(self.symbol.split('/')[1], {}).get('free', 0)
        raw_amount = free_balance * self.trade_fraction / price
        # Round to precision
        amount = float(round(raw_amount, int(self.amount_precision)))
        # Check minimum
        if amount < self.min_amount:
            self.logger.warning(
                "Calculated amount %.8f below minimum %.8f; skipping open.",
                amount, self.min_amount
            )
            return
        try:
            order = exchange.create_market_buy_order(self.symbol, amount)
            exec_price = float(order.get('average') or order.get('price') or price)
            self.position = 'long'
            self.entry_price = exec_price
            self.position_size = amount
            self.last_trade_time = time.time()
            self.logger.info(
                "Opened long: size=%.*f @ entry=%.4f",
                self.amount_precision,
                amount,
                exec_price
            )
        except ExchangeError as e:
            self.logger.error("Failed to open position: %s", e)

    def close_position(self, price: float) -> None:
        if not self.position or not self.position_size or not self.entry_price:
            return
        try:
            if self.position == 'long':
                order = exchange.create_market_sell_order(self.symbol, self.position_size)
            else:
                order = exchange.create_market_buy_order(self.symbol, self.position_size)
            exit_price = float(order.get('average') or order.get('price') or price)
            pnl = (exit_price - self.entry_price) * self.position_size * (1 if self.position == 'long' else -1)
            self.logger.info(
                "Closed %s: size=%.*f @ exit=%.4f | PnL=%.4f",
                self.position,
                self.amount_precision,
                self.position_size,
                exit_price,
                pnl
            )
        except ExchangeError as e:
            self.logger.error("Failed to close position: %s", e)
        finally:
            self.position = None
            self.entry_price = None
            self.position_size = None
            self.last_trade_time = time.time()

    def _handle_cycle(self) -> None:
        bars = self.fetch_with_retry()
        if not bars:
            return
        closes, highs, lows = self.extract_prices(bars)
        if len(closes) < 20:
            self.logger.warning("Insufficient bars (<20). Skipping analysis.")
            return
        price = closes[-1]
        fib = calculate_fibonacci_levels(max(highs[-20:]), min(lows[-20:]))
        signal = evaluate_signals(closes, fib)
        self.logger.info("Price=%.4f | Signal=%s", price, signal)
        if signal == 'BUY':
            if self.position != 'long':
                self.close_position(price)
                self.open_position(price)
        elif signal == 'SELL':
            if self.position != 'short':
                self.close_position(price)
                self.open_position(price)
        self.reset_position_if_stale()

    def reset_position_if_stale(self) -> None:
        if self.position and time.time() - self.last_trade_time > self.reset_timeout:
            last_price = exchange.fetch_ticker(self.symbol).get('last') or 0
            self.logger.info("Stale position; closing at last price %.4f", last_price)
            self.close_position(last_price)

    def run(self) -> None:
        setup_logging()
        self.logger.info("Starting TradingBot for %s", self.symbol)
        self.running = True
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, 'running', False))
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, 'running', False))
        while self.running:
            try:
                self._handle_cycle()
            except Exception as e:
                self.logger.error("Error in cycle: %s", e, exc_info=True)
            time.sleep(self.retry_delay)
        try:
            exchange.close()
            self.logger.info("Exchange connection closed.")
        except Exception as e:
            self.logger.warning("Error closing exchange: %s", e)


if __name__ == '__main__':
    bot = TradingBot()
    bot.run()
