import yfinance as yf
import pandas as pd
import time
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from ta.volatility import AverageTrueRange

# === Strategy Parameters ===
MIN_AVG_VOLUME = 1_000_000      # Minimum average volume over the last N days
RSI_LOWER = 40                # Lower bound for RSI filter
RSI_UPPER = 60                # Upper bound for RSI filter
RR_THRESHOLD = 2.0            # Minimum required reward-to-risk ratio
SWING_LOOKBACK = 20           # Lookback period for swing high calculation

RSI_WEIGHT = 0.30             # Weight for the RSI score component
TREND_WEIGHT = 0.25           # Weight for the trend score component
RR_WEIGHT = 0.15              # Weight for the reward-to-risk score component
TOTAL_SCORE_DIVISOR = RSI_WEIGHT + TREND_WEIGHT + RR_WEIGHT  # Divisor to normalize the score

# === Step 1: Load Tickers (S&P 500 + NASDAQ 100) ===
sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/NASDAQ-100')[4]

tickers = list(set(sp500['Symbol'].tolist() + nasdaq100['Ticker'].tolist()))
tickers = [ticker.replace('.', '-') for ticker in tickers]

valid_setups = []

for ticker in tickers:
    try:
        # Download data with auto_adjust explicitly set to False
        df = yf.download(ticker, period='3mo', interval='1d', progress=False, auto_adjust=False)
        if df.shape[0] < 50:
            continue

        df.dropna(inplace=True)

        # Force key columns to be 1D Series
        close_series = pd.Series(df['Close'].values.flatten(), index=df.index)
        high_series = pd.Series(df['High'].values.flatten(), index=df.index)
        low_series = pd.Series(df['Low'].values.flatten(), index=df.index)
        vol_series = pd.Series(df['Volume'].values.flatten(), index=df.index)

        # Calculate Indicators
        rsi_series = RSIIndicator(close_series, window=14).rsi()
        sma20_series = SMAIndicator(close_series, window=20).sma_indicator()
        sma50_series = SMAIndicator(close_series, window=50).sma_indicator()
        atr_series = AverageTrueRange(high_series, low_series, close_series, window=14).average_true_range()

        # Extract latest values as scalars
        current_price = float(close_series.iloc[-1])
        rsi_val = float(rsi_series.iloc[-1])
        sma20 = float(sma20_series.iloc[-1])
        sma50 = float(sma50_series.iloc[-1])
        atr_val = float(atr_series.iloc[-1])

        # Liquidity Filter
        avg_volume = float(vol_series[-SWING_LOOKBACK:].mean())
        if avg_volume < MIN_AVG_VOLUME:
            continue

        # RSI Filter
        if not (RSI_LOWER <= rsi_val <= RSI_UPPER):
            continue

        # Trend Filter
        trend_pass = current_price > sma20 and current_price > sma50
        if not trend_pass:
            continue

        # Reward-to-Risk Estimate with adjusted target
        swing_high = float(df['High'][-SWING_LOOKBACK:].max().iloc[0])
        adj_target = current_price + 0.90 * (swing_high - current_price)
        reward = adj_target - current_price
        risk = atr_val
        rr_ratio = reward / risk if risk != 0 else 0
        rr_pass = rr_ratio >= RR_THRESHOLD

        # Scoring
        rsi_score = 1 - abs(50 - rsi_val) / 10
        trend_score = 1.0 if trend_pass else 0.0
        rr_score = 1.0 if rr_pass else 0.0
        total_score = (rsi_score * RSI_WEIGHT) + (trend_score * TREND_WEIGHT) + (rr_score * RR_WEIGHT)
        normalized_score = total_score / TOTAL_SCORE_DIVISOR

        valid_setups.append({
            'Ticker': ticker,
            'Price': round(current_price, 2),
            'RSI': round(rsi_val, 2),
            'ATR': round(atr_val, 2),
            'SMA20': round(sma20, 2),
            'SMA50': round(sma50, 2),
            'SwingHigh': round(swing_high, 2),
            'AdjTarget': round(adj_target, 2),
            'PotentialR': round(reward, 2),
            'PotentialRisk': round(risk, 2),
            'R:R': round(rr_ratio, 2),
            'Total_Score': round(normalized_score, 4)
        })

        time.sleep(0.25) # Be Nice to Yahoo API

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

results_df = pd.DataFrame(valid_setups)
results_df = results_df.sort_values(by='Total_Score', ascending=False)

print("\nTop Swing Trade Candidates (ranked by strategy fit score):\n")
print(results_df.head(10))