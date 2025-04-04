# Trade Setup Finder

**Trade Setup Finder** is a Python-based tool designed to identify potential trade setups using technical analysis. By leveraging Yahoo Finance data and calculating key technical indicators such as RSI, SMA, and ATR, this tool analyzes stocks from the S&P 500 and NASDAQ-100 to find high-potential candidates.

## Features

### Data Integration
- Automatically retrieves historical stock data from Yahoo Finance via the `yfinance` library.

### Technical Analysis
- Computes essential indicators including RSI, 20- and 50-day SMA, and ATR using the `ta` library.

### Customizable Filters
- Easily adjust strategy parameters like liquidity, RSI range, trend criteria, and reward-to-risk thresholds—all defined as variables at the top of the script.

### Composite Scoring
- Ranks trade setups using a weighted scoring system that evaluates momentum, trend strength, and risk/reward ratios.

### Flexible Strategy
- Fine-tune and extend the approach to suit your trading style with straightforward parameter modifications.
