# 🚀 CryptoTrader

**CryptoTrader** is a fully Python-based cryptocurrency trading bot designed to automate trading strategies using real-time market data. It supports simple moving averages and Fibonacci retracement levels to identify BUY/SELL signals and execute trades automatically.

---

## 🔧 Features

- ✅ **Automated Trading** – Executes trades based on strategy signals (MA + Fibonacci).
- 🐍 **Pure Python** – No complex dependencies or external services.
- ↻ **Real-Time Market Data** – Integrated with [Binance](https://www.binance.com/) via the `ccxt` library.
- ⚙️ **Strategy-Driven** – Easily extend or modify strategies in the `strategy.py` file.
- 📈 **Logging** – Clean, timestamped logs for live monitoring and historical analysis.
- 🔒 **Secure Config** – Uses `.env` for sensitive keys to keep your API credentials safe.

---

## 💠 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/regularnmae/CryptoTrader.git
   cd CryptoTrader
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:

   ```env
   BINANCE_API_KEY=your_api_key
   BINANCE_SECRET_KEY=your_secret_key
   ```

4. **Run the bot**

   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

Edit parameters in `config.py` to adjust bot behavior:

```python
SYMBOL = 'BTC/USDT'
TIMEFRAME = '5m'
LIMIT = 20
RETRY_DELAY = 60
RESET_POSITION_TIMEOUT = 3600
```

You can customize:

- Trading pair (`SYMBOL`)
- Candlestick interval (`TIMEFRAME`)
- Retry and reset logic
- Strategy logic in `strategy.py`

---

## 🧠 Strategy

The default strategy uses:

- **Simple Moving Averages (SMA)** – Fast vs slow crossovers.
- **Fibonacci Retracement Levels** – Determines support/resistance zones.

Signals:

- ✅ **BUY** when price nears 61.8% and short MA > long MA
- ❌ **SELL** when price nears 38.2% and short MA < long MA

---

## 📁 Project Structure

```
CryptoTrader/
├── main.py                # Main trading loop
├── strategy.py            # Signal logic
├── data.py                # Data fetching via ccxt
├── config.py              # Configuration settings
├── logger_config.py       # Logging setup
├── .env                   # Your API keys (excluded from repo)
├── requirements.txt       # Dependencies
└── logs/                  # Log output directory
```

---

## 📋 Requirements

- Python 3.7+
- [ccxt](https://github.com/ccxt/ccxt)
- python-dotenv

Install via:

```bash
pip install ccxt python-dotenv
```

Or:

```bash
pip install -r requirements.txt
```

---

## 🚨 Disclaimer

CryptoTrader is provided **for educational purposes only**. Trading cryptocurrencies carries a high level of risk. Use at your own discretion and **test thoroughly** before deploying with real funds.

---

## 📬 Contact

Questions or feedback? Reach out via [GitHub Issues](https://github.com/regularnmae/CryptoTrader/issues) or email: [zaalasanishvili@gmail.com](mailto\:zaalasanishvili@gmail.com)

---

## ⭐️ Star this repo if you find it useful!

