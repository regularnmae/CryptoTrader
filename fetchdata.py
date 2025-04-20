import ccxt
import csv
import time
from datetime import datetime

# Config
symbol = 'BTC/USDT'
timeframe = '1h'  # 1m, 5m, 1h, 1d, etc.
limit = 500  # Max candles per fetch (Binance limit is 1500)
since = ccxt.binance().parse8601('2023-07-01T00:00:00Z')  # Start time

# Init exchange
exchange = ccxt.binance()
exchange.load_markets()

# Fetching loop
all_ohlcv = []
while True:
    print(f"Fetching candles since {datetime.utcfromtimestamp(since / 1000)}")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    if not ohlcv:
        break
    all_ohlcv.extend(ohlcv)
    since = ohlcv[-1][0] + 1  # move forward by 1 ms after last candle
    time.sleep(exchange.rateLimit / 1000)  # rate limit handling

    if len(ohlcv) < limit:
        break  # no more data to fetch

# Save to CSV
filename = f"data/{symbol.replace('/', '_')}_{timeframe}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    for row in all_ohlcv:
        writer.writerow(row)

print(f"Saved {len(all_ohlcv)} candles to {filename}")
