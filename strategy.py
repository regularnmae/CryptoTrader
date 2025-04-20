import logging
from typing import List, Optional, Dict

DEFAULT_SHORT_PERIOD = 5
DEFAULT_LONG_PERIOD = 10
DEFAULT_TOLERANCE = 0.01  # 1% tolerance

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s")


def calculate_ma(prices: List[float], period: int) -> Optional[float]:
    """Calculate the simple moving average (SMA) for a list of prices."""
    if len(prices) < period:
        logging.debug(f"Insufficient data for SMA calculation with period {period}.")
        return None
    ma = sum(prices[-period:]) / period
    logging.debug(f"Calculated MA for period {period}: {ma:.2f}")
    return ma


def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """Calculate common Fibonacci retracement levels between high and low."""
    diff = high - low
    levels = {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }
    logging.debug(f"Calculated Fibonacci levels: {levels}")
    return levels


def near_fibonacci(target: float, price: float, tol: float = DEFAULT_TOLERANCE) -> bool:
    """Check if a price is within a tolerance of a Fibonacci level."""
    if target == 0:
        return False
    result = abs(price - target) / target <= tol
    logging.debug(f"Checking if price {price} is near Fibonacci level {target}: {result}")
    return result


def evaluate_signals(
    closes: List[float],
    fib_levels: Dict[str, float],
    short_period: int = DEFAULT_SHORT_PERIOD,
    long_period: int = DEFAULT_LONG_PERIOD,
    tolerance: float = DEFAULT_TOLERANCE
) -> str:
    """
    Evaluate trading signal using MA crossover and Fibonacci retracement levels.
    Returns: 'BUY', 'SELL', or 'HOLD'
    """
    short_ma = calculate_ma(closes, short_period)
    long_ma = calculate_ma(closes, long_period)

    if short_ma is None or long_ma is None:
        logging.debug("Insufficient data for MA calculation.")
        return 'HOLD'

    current_price = closes[-1]
    logging.debug(f"Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}, Current Price: {current_price:.2f}")
    logging.debug(f"Fibonacci Levels: {fib_levels}")

    is_near_fib_buy = near_fibonacci(fib_levels['61.8%'], current_price, tolerance)
    is_near_fib_sell = near_fibonacci(fib_levels['38.2%'], current_price, tolerance)

    logging.debug(f"Is price near 61.8% Fibonacci level for BUY: {is_near_fib_buy}")
    logging.debug(f"Is price near 38.2% Fibonacci level for SELL: {is_near_fib_sell}")

    if short_ma > long_ma and is_near_fib_buy:
        logging.info(f"Signal: BUY at price {current_price:.2f}")
        return 'BUY'
    elif short_ma < long_ma and is_near_fib_sell:
        logging.info(f"Signal: SELL at price {current_price:.2f}")
        return 'SELL'
    else:
        logging.info(f"Signal: HOLD at price {current_price:.2f}")
        return 'HOLD'
