# strategy.py
from typing import List, Optional, Dict
import logging

DEFAULT_SHORT_PERIOD = 5
DEFAULT_LONG_PERIOD = 10
DEFAULT_TOLERANCE = 0.01

def calculate_ma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate the simple moving average (SMA) for a list of prices.
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
    """
    Calculate common Fibonacci retracement levels between high and low.
    """
    diff = high - low
    return {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }

def near_fibonacci(target: float, price: float, tol: float = DEFAULT_TOLERANCE) -> bool:
    """
    Check if a price is within a tolerance of a Fibonacci level.
    """
    if target == 0:
        return False
    return abs(price - target) / target <= tol

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

    if short_ma > long_ma and near_fibonacci(fib_levels['61.8%'], current_price, tolerance):
        return 'BUY'
    elif short_ma < long_ma and near_fibonacci(fib_levels['38.2%'], current_price, tolerance):
        return 'SELL'
    else:
        return 'HOLD'
