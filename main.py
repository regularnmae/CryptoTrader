#!/usr/bin/env python3

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

        # Load market precision and limits
        markets = exchange.load_markets()
        market = exchange.markets.get(self.symbol)
        if not market:
            self.logger.error(f"Market {self.symbol} not found.")
            raise ValueError(f"Market {self.symbol} not available.")

        # Ensure precision is int and min_amount is float
        self.amount_precision = int(market.get('precision', {}).get('amount', 8))
        self.min_amount = float(market.get('limits', {}).get('amount', {}).get('min', 0))

    @staticmethod
    def extract_prices(bars: List[List[float]]) -> Tuple[List[float], List[float], List[float]]:
        """
        Extract close, high, low prices from OHLCV bars.
        """
        closes = [bar[4] for bar in bars]
        highs = [bar[2] for bar in bars]
        lows = [bar[3] for bar in bars]
        return closes, highs, lows

    def fetch_with_retry(self) -> Optional[List[List[float]]]:
        """
        Fetch OHLCV data with exponential backoff and jitter.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                bars = fetch_data()
                if bars:
                    return bars
                self.logger.warning("Empty data (attempt %d/%d)", attempt, self.max_retries)
            except ExchangeError as e:
                self.logger.warning("Exchange error (attempt %d/%d): %s", attempt, self.max_retries, e)
            except Exception as e:
                self.logger.warning("Unexpected error (attempt %d/%d): %s", attempt, self.max_retries, e)

            backoff = self.retry_delay * (2 ** (attempt - 1))
            sleep_time = backoff + random.uniform(0, self.retry_delay)
            self.logger.debug(f"Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)

        self.logger.error("Failed to fetch data after %d attempts.", self.max_retries)
        return None

    def open_position(self, price: float) -> None:
        """
        Open a long position, respecting minimum amount and precision.
        """
        balance_info = exchange.fetch_balance()
        quote = self.symbol.split('/')[1]
        free_balance = float(balance_info.get(quote, {}).get('free', 0))

        raw_amount = free_balance * self.trade_fraction / price
        amount = round(raw_amount, self.amount_precision)

        if amount < self.min_amount:
            self.logger.warning(
                f"Order amount {amount:.{self.amount_precision}f} below minimum {self.min_amount:.{self.amount_precision}f}. Skipping."
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
                f"Opened long: size={amount:.{self.amount_precision}f} @ price={exec_price:.4f}"
            )
        except ExchangeError as e:
            self.logger.error(f"Open position failed: {e}")

    def close_position(self, price: float) -> None:
        """
        Close existing position and log PnL.
        """
        if not all([self.position, self.position_size, self.entry_price]):
            return

        try:
            if self.position == 'long':
                order = exchange.create_market_sell_order(self.symbol, self.position_size)
            else:
                order = exchange.create_market_buy_order(self.symbol, self.position_size)

            exec_price = float(order.get('average') or order.get('price') or price)
            pnl = (exec_price - self.entry_price) * self.position_size * (1 if self.position == 'long' else -1)

            self.logger.info(
                f"Closed {self.position}: size={self.position_size:.{self.amount_precision}f} @ "
                f"price={exec_price:.4f} | PnL={pnl:.4f}"
            )
        except ExchangeError as e:
            self.logger.error(f"Close position failed: {e}")
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
            self.logger.warning("Insufficient bars (<20). Skipping.")
            return

        price = closes[-1]
        fib_levels = calculate_fibonacci_levels(max(highs[-20:]), min(lows[-20:]))
        signal = evaluate_signals(closes, fib_levels)

        self.logger.info(f"Price={price:.4f} | Signal={signal}")
        self.logger.debug(f"Fib levels={fib_levels}")

        if signal == 'BUY' and self.position != 'long':
            self.close_position(price)
            self.open_position(price)
        elif signal == 'SELL' and self.position != 'short':
            self.close_position(price)
            self.open_position(price)

        self._reset_stale_position()

    def _reset_stale_position(self) -> None:
        """
        Close positions older than reset timeout.
        """
        if self.position and (time.time() - self.last_trade_time) > self.reset_timeout:
            ticker = exchange.fetch_ticker(self.symbol)
            last_price = float(ticker.get('last', 0))
            self.logger.info(f"Stale position closing at last_price={last_price:.4f}")
            self.close_position(last_price)

    def run(self) -> None:
        """
        Main loop: run until a termination signal is received.
        """
        self.logger.info(f"Starting TradingBot for {self.symbol}")
        self.running = True

        signal.signal(signal.SIGINT, lambda *args: setattr(self, 'running', False))
        signal.signal(signal.SIGTERM, lambda *args: setattr(self, 'running', False))

        while self.running:
            try:
                self._handle_cycle()
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}", exc_info=True)
            time.sleep(self.retry_delay)

        try:
            exchange.close()
            self.logger.info("Exchange connection closed.")
        except Exception as e:
            self.logger.warning(f"Error closing exchange: {e}")


def main():
    setup_logging()
    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    main()
