import logging
import pandas as pd
import numpy as np
from typing import Optional
from strategy import calculate_fibonacci_levels, evaluate_signals


class BacktestBot:
    def __init__(
        self,
        initial_balance: float = 10_000.0,
        commission: float = 0.0005,   # 0.05% per trade
        slippage: float = 0.0002      # 0.02% per fill
    ):
        # Setup
        self.start_balance = initial_balance
        self.balance = initial_balance
        self.commission = commission
        self.slippage = slippage

        # State
        self.position: Optional[str]   = None
        self.entry_price: Optional[float] = None
        self.position_size: Optional[float] = None

        # Records
        self.trades = []               # (timestamp, position, entry, exit, pnl)
        self.equity_times = []         # timestamps for equity curve
        self.equity_curve = []         # balance over time

        # Logger
        self.log = logging.getLogger(self.__class__.__name__)

    def load_data(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath, parse_dates=['timestamp'])
        required = {'timestamp','open','high','low','close','volume'}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing columns: {missing}")
        return df

    def run(self, df: pd.DataFrame):
        closes = df['close'].values
        highs  = df['high'].values
        lows   = df['low'].values
        times  = df['timestamp'].values

        # Seed equity curve at time = first bar
        self.equity_times.append(times[0])
        self.equity_curve.append(self.balance)

        for i in range(20, len(df)):
            t = times[i]
            price = closes[i]

            # Apply slippage on the fill price
            slip_price = price * (1 + self.slippage
                                  if self.position=='long'
                                  else 1 - self.slippage
                                  if self.position=='short'
                                  else 1)

            # Fib & signal
            fib = calculate_fibonacci_levels(highs[i-20:i].max(), lows[i-20:i].min())
            sig = evaluate_signals(closes[:i+1].tolist(), fib)

            self.log.info(f"[{t}] signal={sig:<4} price={price:.2f}")
            self.handle_trade(sig, slip_price, t)

            # Record equity after any fill
            self.equity_times.append(t)
            self.equity_curve.append(self.balance)

        # Final close
        if self.position:
            self.close_trade(closes[-1], times[-1])

        self.summary()
        self.export_trades()

    def handle_trade(self, signal: str, price: float, timestamp):
        if signal=='BUY' and self.position!='long':
            self.close_trade(price, timestamp)
            self.open_trade('long', price, timestamp)
        elif signal=='SELL' and self.position!='short':
            self.close_trade(price, timestamp)
            self.open_trade('short', price, timestamp)

    def open_trade(self, position: str, price: float, timestamp):
        # size = 10% of current equity
        stake = self.balance * 0.1
        size  = stake / price
        # commission
        cost = price * size * self.commission
        self.balance -= cost

        self.position = position
        self.entry_price = price
        self.position_size = size

        self.log.info(f"  OPEN {position} @ {price:.2f} size={size:.4f} fee={cost:.2f}")

    def close_trade(self, price: float, timestamp):
        if not self.position:
            return

        # raw PnL
        direction =  1 if self.position=='long' else -1
        pnl = (price - self.entry_price) * self.position_size * direction
        # commission
        cost = price * self.position_size * self.commission
        pnl_net = pnl - cost
        self.balance += pnl_net

        # record
        self.trades.append((timestamp,
                            self.position,
                            self.entry_price,
                            price,
                            pnl_net))
        self.log.info(f"  CLOSE {self.position} @ {price:.2f} PnL={pnl_net:.2f} fee={cost:.2f}")

        # reset
        self.position = None
        self.entry_price = None
        self.position_size = None

    def summary(self):
        df_eq = pd.DataFrame({
            'timestamp': self.equity_times,
            'balance':   self.equity_curve
        }).set_index('timestamp')

        # Compute returns
        df_eq['returns'] = df_eq['balance'].pct_change().fillna(0)
        sharpe = df_eq['returns'].mean() / df_eq['returns'].std() * np.sqrt(252*24*12)  # annualized for 5m bars
        peak   = df_eq['balance'].cummax()
        dd     = (df_eq['balance'] - peak) / peak
        max_dd = dd.min()

        self.log.info("--- SUMMARY ---")
        self.log.info(f"Start: {self.start_balance:.2f}")
        self.log.info(f"End:   {self.balance:.2f}")
        self.log.info(f"Trades: {len(self.trades)}")
        self.log.info(f"Sharpe Ratio: {sharpe:.2f}")
        self.log.info(f"Max Drawdown: {max_dd:.2%}")

    def export_trades(self, filename='trades.csv'):
        df = pd.DataFrame(self.trades,
                          columns=['timestamp','position','entry','exit','pnl'])
        df.to_csv(filename, index=False)
        self.log.info(f"Trades → {filename}")


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(message)s")
    bot = BacktestBot()
    df  = bot.load_data("data/BTC_USDT_1d.csv")
    bot.run(df)
