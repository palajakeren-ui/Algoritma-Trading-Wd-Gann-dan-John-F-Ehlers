"""
Yahoo Finance Data Feed for Open Terminal
==========================================
Provides real-time fundamental data using yfinance library.
Falls back to comprehensive simulated data when yfinance is unavailable.

Usage:
    from core.yahoo_finance_feed import get_yahoo_fundamental, get_yahoo_quote

Supports: Stocks, ETFs, Forex, Crypto, Bonds, Indices, Commodities
"""

import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# Try importing yfinance
# ────────────────────────────────────────────────────────────────
_HAS_YFINANCE = False
try:
    import yfinance as yf
    _HAS_YFINANCE = True
    logger.info("yfinance available — Yahoo Finance LIVE data enabled")
except ImportError:
    logger.warning("yfinance not installed — using simulated Yahoo data. Install with: pip install yfinance")

# ────────────────────────────────────────────────────────────────
# Symbol mapping: internal symbol → Yahoo Finance ticker
# ────────────────────────────────────────────────────────────────
YAHOO_SYMBOL_MAP = {
    # Crypto → Yahoo tickers
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD",
    "XRPUSDT": "XRP-USD",
    "ADAUSDT": "ADA-USD",
    "DOGEUSDT": "DOGE-USD",
    "AVAXUSDT": "AVAX-USD",
    "DOTUSDT": "DOT-USD",
    "MATICUSDT": "MATIC-USD",
    "LINKUSDT": "LINK-USD",
    "ATOMUSDT": "ATOM-USD",
    "UNIUSDT": "UNI-USD",
    "AAVEUSDT": "AAVE-USD",
    "LTCUSDT": "LTC-USD",
    "NEARUSDT": "NEAR-USD",
    "APTUSDT": "APT-USD",
    "SUIUSDT": "SUI20947-USD",
    "ARBUSDT": "ARB11841-USD",
    "OPUSDT": "OP-USD",
    "INJUSDT": "INJ-USD",
    "SHIBUSDT": "SHIB-USD",
    "FETUSDT": "FET-USD",
    "TRXUSDT": "TRX-USD",
    "FILUSDT": "FIL-USD",
    "ICPUSDT": "ICP-USD",
    "HBARUSDT": "HBAR-USD",
    "VETUSDT": "VET-USD",
    "XLMUSDT": "XLM-USD",
    "ALGOUSDT": "ALGO-USD",
    "SANDUSDT": "SAND-USD",
    "MANAUSDT": "MANA-USD",
    "PEPEUSDT": "PEPE24478-USD",
    "RENDERUSDT": "RNDR-USD",
    "TIAUSDT": "TIA22861-USD",
    
    # Forex → Yahoo tickers
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X",
    "USDCAD": "USDCAD=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "AUDJPY": "AUDJPY=X",
    "EURCHF": "EURCHF=X",
    "USDMXN": "USDMXN=X",
    "USDZAR": "USDZAR=X",
    "USDTRY": "USDTRY=X",
    "USDSGD": "USDSGD=X",
    
    # Stocks → direct tickers
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "AMZN": "AMZN",
    "NVDA": "NVDA",
    "META": "META",
    "TSLA": "TSLA",
    "JPM": "JPM",
    "V": "V",
    "JNJ": "JNJ",
    "WMT": "WMT",
    "PG": "PG",
    "MA": "MA",
    "DIS": "DIS",
    "BAC": "BAC",
    "NFLX": "NFLX",
    "AMD": "AMD",
    "INTC": "INTC",
    "CRM": "CRM",
    "PYPL": "PYPL",
    
    # Bonds → Yahoo tickers
    "US10Y": "^TNX",
    "US2Y": "^IRX",
    "US5Y": "^FVX",
    "US30Y": "^TYX",
    "TLT": "TLT",
    "HYG": "HYG",
    
    # Indices → Yahoo tickers
    "NDX": "^NDX",
    "DJI": "^DJI",
    "VIX": "^VIX",
    "DAX": "^GDAXI",
    "N225": "^N225",
    "FTSE": "^FTSE",
    "RUT": "^RUT",
    
    # Commodities → Yahoo tickers
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "WTIUSD": "CL=F",
    "BRENTUSD": "BZ=F",
    "NATGASUSD": "NG=F",
    "COPPERUSD": "HG=F",
    "PLATINUMUSD": "PL=F",
    "PALLADIUMUSD": "PA=F",
    "WHEATUSD": "ZW=F",
    "CORNUSD": "ZC=F",
    "SOYBEANUSD": "ZS=F",
    "COFFEEUSD": "KC=F",
    "COTTONUSD": "CT=F",
}

# ────────────────────────────────────────────────────────────────
# Realistic seed data for simulated fallback
# ────────────────────────────────────────────────────────────────
_SIMULATED_FUNDAMENTALS: Dict[str, Dict[str, Any]] = {
    # -- Major Stocks --
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics",
             "marketCap": 2.95e12, "pe": 29.5, "eps": 6.42, "dividend": 0.52, "beta": 1.21,
             "revenue": 383.29e9, "netIncome": 97.0e9, "profitMargin": 25.3, "roe": 171.0,
             "debtToEquity": 176.3, "freeCashFlow": 110.5e9, "employees": 164000,
             "52wHigh": 199.62, "52wLow": 164.08, "avgVolume": 54.2e6, "description":
             "Apple Inc. designs, manufactures, and markets smartphones, personal computers, "
             "tablets, wearables, and accessories worldwide."},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "industry": "Software",
             "marketCap": 3.12e12, "pe": 36.2, "eps": 11.86, "dividend": 0.75, "beta": 0.89,
             "revenue": 227.6e9, "netIncome": 82.5e9, "profitMargin": 36.3, "roe": 39.2,
             "debtToEquity": 39.5, "freeCashFlow": 63.3e9, "employees": 221000},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors",
             "marketCap": 2.15e12, "pe": 65.8, "eps": 12.96, "dividend": 0.04, "beta": 1.68,
             "revenue": 60.9e9, "netIncome": 29.8e9, "profitMargin": 48.9, "roe": 91.5,
             "debtToEquity": 41.2, "freeCashFlow": 27.0e9, "employees": 29600},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Services",
              "marketCap": 1.95e12, "pe": 24.8, "eps": 6.52, "dividend": 0.0, "beta": 1.05,
              "revenue": 307.4e9, "netIncome": 73.8e9, "profitMargin": 24.0, "roe": 28.4,
              "debtToEquity": 11.1, "freeCashFlow": 69.5e9, "employees": 182502},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "E-Commerce",
             "marketCap": 1.92e12, "pe": 58.5, "eps": 3.29, "dividend": 0.0, "beta": 1.15,
             "revenue": 574.8e9, "netIncome": 30.4e9, "profitMargin": 5.3, "roe": 18.9,
             "debtToEquity": 88.2, "freeCashFlow": 32.2e9, "employees": 1525000},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers",
             "marketCap": 652e9, "pe": 42.5, "eps": 4.73, "dividend": 0.0, "beta": 2.05,
             "revenue": 96.8e9, "netIncome": 15.0e9, "profitMargin": 15.5, "roe": 27.1,
             "debtToEquity": 11.5, "freeCashFlow": 4.4e9, "employees": 140473},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Social Media",
             "marketCap": 1.32e12, "pe": 25.3, "eps": 20.8, "dividend": 0.5, "beta": 1.22,
             "revenue": 134.9e9, "netIncome": 39.1e9, "profitMargin": 29.0, "roe": 33.4,
             "debtToEquity": 28.5, "freeCashFlow": 43.0e9, "employees": 67317},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial Services", "industry": "Banking",
            "marketCap": 580e9, "pe": 11.8, "eps": 17.35, "dividend": 4.0, "beta": 1.08,
            "revenue": 158.1e9, "netIncome": 49.6e9, "profitMargin": 31.4, "roe": 17.0,
            "debtToEquity": 148.5, "freeCashFlow": 28.0e9, "employees": 309926},
    "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services", "industry": "Entertainment",
             "marketCap": 270e9, "pe": 45.2, "eps": 14.08, "dividend": 0.0, "beta": 1.35,
             "revenue": 33.7e9, "netIncome": 5.4e9, "profitMargin": 16.0, "roe": 26.8,
             "debtToEquity": 72.3, "freeCashFlow": 6.9e9, "employees": 13000},
    
    # -- Crypto --
    "BTCUSDT": {"name": "Bitcoin", "sector": "Cryptocurrency", "industry": "Layer 1",
                "marketCap": 1.82e12, "circulatingSupply": 19.6e6, "maxSupply": 21e6,
                "dominance": 52.5, "hashRate": "623 EH/s", "difficulty": "75.5T",
                "nvtRatio": 42.5, "stockToFlow": 56.2, "activeAddresses": 1050000,
                "feesAvg24h": 2.15, "stakingApy": None, "volatility30d": 45.2},
    "ETHUSDT": {"name": "Ethereum", "sector": "Cryptocurrency", "industry": "Smart Contract Platform",
                "marketCap": 420e9, "circulatingSupply": 120.2e6, "maxSupply": None,
                "dominance": 16.8, "hashRate": None, "stakingApy": 4.2,
                "nvtRatio": 38.0, "activeAddresses": 650000, "tvlDefi": 65.2e9,
                "feesAvg24h": 4.50, "volatility30d": 55.3, "burnRate": "2.5 ETH/min"},
    "SOLUSDT": {"name": "Solana", "sector": "Cryptocurrency", "industry": "Smart Contract Platform",
                "marketCap": 78e9, "circulatingSupply": 440e6, "dominance": 3.1,
                "stakingApy": 7.1, "activeAddresses": 420000, "tvlDefi": 8.5e9,
                "tps": 4000, "volatility30d": 62.5},
    
    # -- Forex descriptions --
    "EURUSD": {"name": "EUR/USD", "sector": "Forex", "industry": "Major Pair",
               "description": "Euro vs US Dollar - the most traded currency pair globally."},
    "GBPUSD": {"name": "GBP/USD", "sector": "Forex", "industry": "Major Pair",
               "description": "British Pound vs US Dollar (Cable)."},
    "USDJPY": {"name": "USD/JPY", "sector": "Forex", "industry": "Major Pair",
               "description": "US Dollar vs Japanese Yen - key Asia-Pacific pair."},
    
    # -- Bonds --
    "US10Y": {"name": "US 10-Year Treasury Note", "sector": "Fixed Income", "industry": "Government Bond",
              "couponRate": 4.25, "maturityDate": "2034-02-15", "yieldToMaturity": 4.28,
              "duration": 7.8, "convexity": 0.72, "creditRating": "AAA",
              "description": "US Treasury 10-year benchmark bond yield."},
    "US30Y": {"name": "US 30-Year Treasury Bond", "sector": "Fixed Income", "industry": "Government Bond",
              "couponRate": 4.375, "maturityDate": "2054-02-15", "yieldToMaturity": 4.45,
              "duration": 17.2, "convexity": 3.85, "creditRating": "AAA"},
    "TLT": {"name": "iShares 20+ Year Treasury Bond ETF", "sector": "Fixed Income", "industry": "Bond ETF",
            "marketCap": 50.5e9, "pe": None, "dividend": 3.65, "beta": -0.15,
            "aum": 50.5e9, "expenseRatio": 0.15, "avgDuration": 16.8},
    
    # -- Commodities --
    "XAUUSD": {"name": "Gold Spot / USD", "sector": "Commodities", "industry": "Precious Metals",
               "description": "Spot gold price in US dollars per troy ounce."},
    "WTIUSD": {"name": "WTI Crude Oil", "sector": "Commodities", "industry": "Energy",
               "description": "West Texas Intermediate crude oil futures."},
}

# In-memory cache for Yahoo data
_yahoo_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 300  # 5-minute cache


def _get_yahoo_ticker(symbol: str) -> str:
    """Map internal symbol to Yahoo Finance ticker."""
    return YAHOO_SYMBOL_MAP.get(symbol, symbol)


def _is_cache_valid(symbol: str) -> bool:
    """Check if cached data is still fresh."""
    if symbol not in _yahoo_cache:
        return False
    cached = _yahoo_cache[symbol]
    return (time.time() - cached.get('_fetch_time', 0)) < _CACHE_TTL_SECONDS


# ────────────────────────────────────────────────────────────────
# LIVE Yahoo Finance data fetch
# ────────────────────────────────────────────────────────────────
def _fetch_live_yahoo(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch live data from Yahoo Finance via yfinance."""
    if not _HAS_YFINANCE:
        return None
    
    yahoo_ticker = _get_yahoo_ticker(symbol)
    
    try:
        ticker = yf.Ticker(yahoo_ticker)
        info = ticker.info or {}
        
        if not info or info.get('regularMarketPrice') is None:
            logger.warning(f"No data from Yahoo for {yahoo_ticker}")
            return None
        
        # Determine asset type
        quote_type = info.get('quoteType', 'EQUITY')
        
        result: Dict[str, Any] = {
            '_fetch_time': time.time(),
            '_source': 'yahoo_finance_live',
            'name': info.get('longName') or info.get('shortName') or symbol,
            'symbol': symbol,
            'yahooTicker': yahoo_ticker,
            'quoteType': quote_type,
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange', ''),
            'timezone': info.get('exchangeTimezoneName', ''),
            
            # Price data
            'price': info.get('regularMarketPrice') or info.get('currentPrice'),
            'previousClose': info.get('regularMarketPreviousClose') or info.get('previousClose'),
            'open': info.get('regularMarketOpen') or info.get('open'),
            'dayHigh': info.get('regularMarketDayHigh') or info.get('dayHigh'),
            'dayLow': info.get('regularMarketDayLow') or info.get('dayLow'),
            'volume': info.get('regularMarketVolume') or info.get('volume'),
            'avgVolume': info.get('averageDailyVolume10Day') or info.get('averageVolume'),
            'bid': info.get('bid'),
            'ask': info.get('ask'),
            'bidSize': info.get('bidSize'),
            'askSize': info.get('askSize'),
            
            # 52-week range
            '52wHigh': info.get('fiftyTwoWeekHigh'),
            '52wLow': info.get('fiftyTwoWeekLow'),
            'fiftyDayAvg': info.get('fiftyDayAverage'),
            'twoHundredDayAvg': info.get('twoHundredDayAverage'),
        }
        
        # Equity-specific fundamentals
        if quote_type in ('EQUITY', 'ETF'):
            result.update({
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'description': info.get('longBusinessSummary', ''),
                'marketCap': info.get('marketCap'),
                'enterpriseValue': info.get('enterpriseValue'),
                
                # Valuation
                'peRatio': info.get('trailingPE'),
                'forwardPe': info.get('forwardPE'),
                'pegRatio': info.get('pegRatio'),
                'pbRatio': info.get('priceToBook'),
                'psRatio': info.get('priceToSalesTrailing12Months'),
                'evToRevenue': info.get('enterpriseToRevenue'),
                'evToEbitda': info.get('enterpriseToEbitda'),
                
                # Profitability
                'eps': info.get('trailingEps'),
                'forwardEps': info.get('forwardEps'),
                'revenue': info.get('totalRevenue'),
                'revenuePerShare': info.get('revenuePerShare'),
                'grossMargin': _pct(info.get('grossMargins')),
                'operatingMargin': _pct(info.get('operatingMargins')),
                'profitMargin': _pct(info.get('profitMargins')),
                'netIncome': info.get('netIncomeToCommon'),
                
                # Growth
                'revenueGrowth': _pct(info.get('revenueGrowth')),
                'earningsGrowth': _pct(info.get('earningsGrowth')),
                'earningsQuarterlyGrowth': _pct(info.get('earningsQuarterlyGrowth')),
                
                # Financial health
                'totalCash': info.get('totalCash'),
                'totalDebt': info.get('totalDebt'),
                'debtToEquity': info.get('debtToEquity'),
                'currentRatio': info.get('currentRatio'),
                'quickRatio': info.get('quickRatio'),
                'roe': _pct(info.get('returnOnEquity')),
                'roa': _pct(info.get('returnOnAssets')),
                'freeCashFlow': info.get('freeCashflow'),
                'operatingCashFlow': info.get('operatingCashflow'),
                
                # Dividends
                'dividendYield': _pct(info.get('dividendYield')),
                'dividendRate': info.get('dividendRate'),
                'payoutRatio': _pct(info.get('payoutRatio')),
                'exDividendDate': info.get('exDividendDate'),
                
                # Risk
                'beta': info.get('beta'),
                
                # Shares
                'sharesOutstanding': info.get('sharesOutstanding'),
                'floatShares': info.get('floatShares'),
                'shortRatio': info.get('shortRatio'),
                'shortPercentFloat': _pct(info.get('shortPercentOfFloat')),
                'insiderHolding': _pct(info.get('heldPercentInsiders')),
                'institutionHolding': _pct(info.get('heldPercentInstitutions')),
                
                # Targets
                'targetHighPrice': info.get('targetHighPrice'),
                'targetLowPrice': info.get('targetLowPrice'),
                'targetMeanPrice': info.get('targetMeanPrice'),
                'targetMedianPrice': info.get('targetMedianPrice'),
                'numberOfAnalystOpinions': info.get('numberOfAnalystOpinions'),
                'recommendationKey': info.get('recommendationKey'),
                'recommendationMean': info.get('recommendationMean'),
                
                # Company info
                'employees': info.get('fullTimeEmployees'),
                'website': info.get('website'),
                'city': info.get('city'),
                'country': info.get('country'),
            })
        
        # Crypto-specific
        elif quote_type == 'CRYPTOCURRENCY':
            result.update({
                'sector': 'Cryptocurrency',
                'marketCap': info.get('marketCap'),
                'circulatingSupply': info.get('circulatingSupply'),
                'volume24h': info.get('volume24Hr'),
                'startDate': info.get('startDate'),
                'description': info.get('description', ''),
            })
        
        logger.info(f"Yahoo Finance LIVE data fetched for {symbol} ({yahoo_ticker})")
        return result
        
    except Exception as e:
        logger.warning(f"Yahoo Finance fetch error for {symbol}: {e}")
        return None


def _pct(value) -> Optional[float]:
    """Convert decimal to percentage if value exists."""
    if value is None:
        return None
    try:
        return round(float(value) * 100, 2)
    except (TypeError, ValueError):
        return None


# ────────────────────────────────────────────────────────────────
# Simulated fallback with realistic data
# ────────────────────────────────────────────────────────────────
def _generate_simulated(symbol: str, base_price: float = 100.0) -> Dict[str, Any]:
    """Generate comprehensive simulated fundamental data."""
    
    # Check if we have seed data
    seed = _SIMULATED_FUNDAMENTALS.get(symbol, {})
    
    # Determine asset category
    is_crypto = symbol.endswith("USDT") or symbol in ("BTC-USD", "ETH-USD")
    is_forex = any(symbol.startswith(p) for p in ("EUR", "GBP", "USD", "AUD", "NZD", "CHF", "CAD"))
    is_bond = any(symbol.startswith(p) for p in ("US1", "US2", "US3", "US5", "DE1", "GB1", "JP1", "IT1", "FR1", "AU1")) or symbol in ("TLT", "HYG")
    is_commodity = symbol.endswith("USD") and not is_forex and not is_crypto
    is_stock = not is_crypto and not is_forex and not is_bond and not is_commodity
    
    if is_crypto:
        return _sim_crypto(symbol, base_price, seed)
    elif is_forex:
        return _sim_forex(symbol, base_price, seed)
    elif is_bond:
        return _sim_bond(symbol, base_price, seed)
    elif is_commodity:
        return _sim_commodity(symbol, base_price, seed)
    else:
        return _sim_stock(symbol, base_price, seed)


def _sim_stock(symbol: str, price: float, seed: dict) -> Dict[str, Any]:
    """Simulated stock fundamental data."""
    mcap = seed.get("marketCap", price * random.uniform(5e9, 50e9) / 100)
    pe = seed.get("pe", round(random.uniform(12, 45), 1))
    eps = seed.get("eps", round(price / pe if pe > 0 else 5.0, 2))
    
    return {
        '_source': 'simulated_yahoo',
        'name': seed.get("name", symbol),
        'symbol': symbol,
        'quoteType': 'EQUITY',
        'sector': seed.get("sector", random.choice(["Technology", "Healthcare", "Finance", "Consumer"])),
        'industry': seed.get("industry", ""),
        'description': seed.get("description", f"{symbol} is a publicly traded company listed on major US exchanges."),
        'price': price,
        'marketCap': mcap,
        'enterpriseValue': mcap * random.uniform(0.95, 1.15),
        
        # Valuation
        'peRatio': pe,
        'forwardPe': round(pe * random.uniform(0.8, 0.95), 1),
        'pegRatio': round(random.uniform(0.8, 2.5), 2),
        'pbRatio': round(random.uniform(2, 12), 1),
        'psRatio': round(random.uniform(3, 15), 1),
        'evToRevenue': round(random.uniform(4, 20), 1),
        'evToEbitda': round(random.uniform(10, 35), 1),
        
        # Earnings
        'eps': eps,
        'forwardEps': round(eps * random.uniform(1.05, 1.2), 2),
        'revenue': seed.get("revenue", mcap * random.uniform(0.15, 0.4)),
        'revenuePerShare': round(random.uniform(15, 80), 2),
        'grossMargin': round(random.uniform(40, 75), 1),
        'operatingMargin': round(random.uniform(15, 40), 1),
        'profitMargin': seed.get("profitMargin", round(random.uniform(10, 35), 1)),
        'netIncome': seed.get("netIncome", mcap * random.uniform(0.03, 0.08)),
        
        # Growth
        'revenueGrowth': round(random.uniform(-5, 35), 1),
        'earningsGrowth': round(random.uniform(-10, 50), 1),
        'earningsQuarterlyGrowth': round(random.uniform(-15, 60), 1),
        
        # Balance sheet
        'totalCash': mcap * random.uniform(0.05, 0.15),
        'totalDebt': mcap * random.uniform(0.1, 0.4),
        'debtToEquity': seed.get("debtToEquity", round(random.uniform(20, 150), 1)),
        'currentRatio': round(random.uniform(1.0, 3.0), 2),
        'quickRatio': round(random.uniform(0.8, 2.5), 2),
        'roe': seed.get("roe", round(random.uniform(12, 40), 1)),
        'roa': round(random.uniform(5, 20), 1),
        'freeCashFlow': seed.get("freeCashFlow", mcap * random.uniform(0.02, 0.06)),
        'operatingCashFlow': mcap * random.uniform(0.04, 0.1),
        
        # Dividends
        'dividendYield': seed.get("dividend", round(random.uniform(0, 3), 2)),
        'dividendRate': round(random.uniform(0, 8), 2),
        'payoutRatio': round(random.uniform(15, 60), 1),
        
        # Risk
        'beta': seed.get("beta", round(random.uniform(0.7, 1.8), 2)),
        '52wHigh': seed.get("52wHigh", price * random.uniform(1.05, 1.35)),
        '52wLow': seed.get("52wLow", price * random.uniform(0.6, 0.9)),
        'fiftyDayAvg': price * random.uniform(0.95, 1.05),
        'twoHundredDayAvg': price * random.uniform(0.85, 1.1),
        
        # Shares & ownership
        'sharesOutstanding': mcap / price if price > 0 else 1e9,
        'shortRatio': round(random.uniform(1, 5), 1),
        'shortPercentFloat': round(random.uniform(1, 8), 1),
        'insiderHolding': round(random.uniform(1, 15), 1),
        'institutionHolding': round(random.uniform(60, 90), 1),
        
        # Analyst
        'targetHighPrice': price * random.uniform(1.2, 1.5),
        'targetLowPrice': price * random.uniform(0.7, 0.9),
        'targetMeanPrice': price * random.uniform(1.05, 1.25),
        'numberOfAnalystOpinions': random.randint(15, 45),
        'recommendationKey': random.choice(["buy", "strong_buy", "hold", "buy"]),
        'recommendationMean': round(random.uniform(1.5, 3.0), 1),
        
        'employees': seed.get("employees", random.randint(5000, 200000)),
        'volume': round(random.uniform(5e6, 100e6)),
        'avgVolume': seed.get("avgVolume", round(random.uniform(10e6, 80e6))),
    }


def _sim_crypto(symbol: str, price: float, seed: dict) -> Dict[str, Any]:
    """Simulated crypto fundamental data."""
    mcap = seed.get("marketCap", price * random.uniform(1e8, 5e10))
    
    return {
        '_source': 'simulated_yahoo',
        'name': seed.get("name", symbol.replace("USDT", "")),
        'symbol': symbol,
        'quoteType': 'CRYPTOCURRENCY',
        'sector': 'Cryptocurrency',
        'industry': seed.get("industry", "Digital Asset"),
        'description': seed.get("description", f"{symbol} cryptocurrency trading pair."),
        'price': price,
        'marketCap': mcap,
        'circulatingSupply': seed.get("circulatingSupply", mcap / price if price > 0 else 1e6),
        'maxSupply': seed.get("maxSupply"),
        'volume24h': round(random.uniform(1e8, 8e10)),
        
        # On-chain metrics
        'dominance': seed.get("dominance", round(random.uniform(0.5, 5), 2)),
        'nvtRatio': seed.get("nvtRatio", round(random.uniform(15, 80), 1)),
        'activeAddresses': seed.get("activeAddresses", round(random.uniform(50000, 1200000))),
        'hashRate': seed.get("hashRate"),
        'stakingApy': seed.get("stakingApy", round(random.uniform(3, 8), 1) if "BTC" not in symbol else None),
        'tvlDefi': seed.get("tvlDefi", round(random.uniform(1e8, 50e9))),
        'stockToFlow': seed.get("stockToFlow"),
        'volatility30d': seed.get("volatility30d", round(random.uniform(30, 85), 1)),
        'sharpeRatio1y': round(random.uniform(0.3, 2.5), 2),
        'feesAvg24h': seed.get("feesAvg24h", round(random.uniform(0.5, 10), 2)),
        'burnRate': seed.get("burnRate"),
        'tps': seed.get("tps"),
        
        '52wHigh': price * random.uniform(1.1, 3.0),
        '52wLow': price * random.uniform(0.1, 0.6),
        'fiftyDayAvg': price * random.uniform(0.85, 1.1),
        'change7d': round(random.uniform(-15, 25), 2),
        'change30d': round(random.uniform(-30, 60), 2),
        'change1y': round(random.uniform(-40, 200), 2),
    }


def _sim_forex(symbol: str, price: float, seed: dict) -> Dict[str, Any]:
    """Simulated forex fundamental data."""
    return {
        '_source': 'simulated_yahoo',
        'name': seed.get("name", f"{symbol[:3]}/{symbol[3:]}"),
        'symbol': symbol,
        'quoteType': 'CURRENCY',
        'sector': 'Forex',
        'industry': seed.get("industry", "FX Major" if len(symbol) == 6 else "FX Cross"),
        'description': seed.get("description", f"{symbol} forex currency pair."),
        'price': price,
        'bid': price * 0.99998,
        'ask': price * 1.00002,
        'spread': round(price * 0.00004, 5),
        'spreadPips': round(random.uniform(0.5, 3.0), 1),
        
        # Forex-specific
        'swapLong': round(random.uniform(-5, 5), 2),
        'swapShort': round(random.uniform(-5, 5), 2),
        'pipValue': round(random.uniform(8, 12), 2),
        'dailyRange': round(price * random.uniform(0.003, 0.012), 4),
        'avgDailyRange20': round(price * random.uniform(0.005, 0.015), 4),
        'correlation_DXY': round(random.uniform(-0.9, 0.9), 2),
        'volatility30d': round(random.uniform(5, 15), 1),
        
        # Interest rate differentials
        'interestRateBase': round(random.uniform(0, 5.5), 2),
        'interestRateQuote': round(random.uniform(0, 5.5), 2),
        'carryReturn': round(random.uniform(-3, 4), 2),
        
        '52wHigh': price * random.uniform(1.02, 1.08),
        '52wLow': price * random.uniform(0.92, 0.98),
        'fiftyDayAvg': price * random.uniform(0.98, 1.02),
        'twoHundredDayAvg': price * random.uniform(0.95, 1.05),
    }


def _sim_bond(symbol: str, price: float, seed: dict) -> Dict[str, Any]:
    """Simulated bond fundamental data."""
    return {
        '_source': 'simulated_yahoo',
        'name': seed.get("name", symbol),
        'symbol': symbol,
        'quoteType': 'BOND',
        'sector': 'Fixed Income',
        'industry': seed.get("industry", "Government Bond"),
        'description': seed.get("description", f"{symbol} fixed income security."),
        'price': price,  # yield %
        
        # Bond-specific
        'yieldToMaturity': seed.get("yieldToMaturity", price),
        'couponRate': seed.get("couponRate", round(price - random.uniform(0, 0.5), 3)),
        'maturityDate': seed.get("maturityDate", "2034-02-15"),
        'duration': seed.get("duration", round(random.uniform(2, 20), 1)),
        'modifiedDuration': round(random.uniform(2, 18), 1),
        'convexity': seed.get("convexity", round(random.uniform(0.1, 4), 2)),
        'creditRating': seed.get("creditRating", random.choice(["AAA", "AA+", "AA", "A+"])),
        'spreadToBenchmark': round(random.uniform(0, 200), 0),
        'dv01': round(random.uniform(0.05, 0.15), 4),
        
        # Yield curve context
        'yield2y': round(random.uniform(3.8, 5.0), 2),
        'yield5y': round(random.uniform(3.5, 4.5), 2),
        'yield10y': round(random.uniform(3.8, 4.5), 2),
        'yield30y': round(random.uniform(4.0, 4.8), 2),
        'yieldCurveSlope': round(random.uniform(-0.5, 0.5), 2),
        
        'previousClose': price + random.uniform(-0.05, 0.05),
        'change1d': round(random.uniform(-0.08, 0.08), 3),
        'change1w': round(random.uniform(-0.15, 0.15), 3),
        'change1m': round(random.uniform(-0.3, 0.3), 3),
    }


def _sim_commodity(symbol: str, price: float, seed: dict) -> Dict[str, Any]:
    """Simulated commodity fundamental data."""
    return {
        '_source': 'simulated_yahoo',
        'name': seed.get("name", symbol),
        'symbol': symbol,
        'quoteType': 'FUTURE',
        'sector': 'Commodities',
        'industry': seed.get("industry", "Commodity"),
        'description': seed.get("description", f"{symbol} commodity contract."),
        'price': price,
        
        # Commodity-specific
        'contractMonth': "Mar 2026",
        'contractExpiry': "2026-03-20",
        'openInterest': round(random.uniform(100000, 800000)),
        'openInterestChange': round(random.uniform(-5000, 5000)),
        'contango': round(random.uniform(-2, 5), 2),
        'inventoryLevel': f"{round(random.uniform(200, 600))}M bbl" if "USD" in symbol and ("WTI" in symbol or "BRENT" in symbol) else None,
        'seasonalPattern': random.choice(["Bullish Q1", "Neutral", "Bearish Q2", "Bullish H2"]),
        
        'volume': round(random.uniform(50000, 500000)),
        'avgVolume': round(random.uniform(80000, 400000)),
        '52wHigh': price * random.uniform(1.05, 1.30),
        '52wLow': price * random.uniform(0.65, 0.90),
        'fiftyDayAvg': price * random.uniform(0.95, 1.05),
        'twoHundredDayAvg': price * random.uniform(0.85, 1.1),
        'volatility30d': round(random.uniform(15, 45), 1),
        
        'change1d': round(random.uniform(-3, 3), 2),
        'change1w': round(random.uniform(-5, 5), 2),
        'change1m': round(random.uniform(-10, 10), 2),
        'changeYtd': round(random.uniform(-20, 30), 2),
    }


# ════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════

def get_yahoo_fundamental(symbol: str, base_price: float = 100.0) -> Dict[str, Any]:
    """
    Get comprehensive fundamental data for a symbol.
    
    Tries Yahoo Finance live data first, falls back to simulated.
    Results are cached for 5 minutes.
    
    Args:
        symbol: Internal symbol (e.g., "AAPL", "BTCUSDT", "EURUSD")
        base_price: Current/seed price for simulation fallback
    
    Returns:
        Dict with fundamental data, always includes '_source' key
    """
    # Check cache first
    if _is_cache_valid(symbol):
        cached = _yahoo_cache[symbol].copy()
        cached['_cached'] = True
        return cached
    
    # Try live Yahoo Finance
    result = _fetch_live_yahoo(symbol)
    
    # Fallback to simulation
    if result is None:
        result = _generate_simulated(symbol, base_price)
    
    # Cache the result
    result['_fetch_time'] = time.time()
    result['_timestamp'] = datetime.now().isoformat()
    _yahoo_cache[symbol] = result
    
    return result


def get_yahoo_quote(symbol: str) -> Dict[str, Any]:
    """
    Get quick price quote from Yahoo Finance.
    
    Returns minimal price data — faster than full fundamental fetch.
    """
    yahoo_ticker = _get_yahoo_ticker(symbol)
    
    if _HAS_YFINANCE:
        try:
            ticker = yf.Ticker(yahoo_ticker)
            info = ticker.info or {}
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            if price:
                return {
                    'success': True,
                    'source': 'yahoo_finance_live',
                    'symbol': symbol,
                    'price': price,
                    'change': info.get('regularMarketChange'),
                    'changePct': info.get('regularMarketChangePercent'),
                    'volume': info.get('regularMarketVolume'),
                    'bid': info.get('bid'),
                    'ask': info.get('ask'),
                    'high': info.get('regularMarketDayHigh'),
                    'low': info.get('regularMarketDayLow'),
                    'timestamp': datetime.now().isoformat(),
                }
        except Exception as e:
            logger.warning(f"Yahoo quote error for {symbol}: {e}")
    
    return {
        'success': True,
        'source': 'simulated',
        'symbol': symbol,
        'price': None,
        'timestamp': datetime.now().isoformat(),
    }


def get_yahoo_status() -> Dict[str, Any]:
    """Get Yahoo Finance feed status."""
    return {
        'yfinanceInstalled': _HAS_YFINANCE,
        'mode': 'live' if _HAS_YFINANCE else 'simulated',
        'cachedSymbols': list(_yahoo_cache.keys()),
        'cacheSize': len(_yahoo_cache),
        'cacheTtlSeconds': _CACHE_TTL_SECONDS,
        'supportedSymbols': len(YAHOO_SYMBOL_MAP),
        'symbolCategories': {
            'crypto': len([s for s in YAHOO_SYMBOL_MAP if s.endswith('USDT')]),
            'forex': len([s for s in YAHOO_SYMBOL_MAP if YAHOO_SYMBOL_MAP[s].endswith('=X')]),
            'stocks': len([s for s in YAHOO_SYMBOL_MAP if YAHOO_SYMBOL_MAP[s] == s]),
            'bonds': len([s for s in YAHOO_SYMBOL_MAP if YAHOO_SYMBOL_MAP[s].startswith('^T') or YAHOO_SYMBOL_MAP[s].startswith('^I') or YAHOO_SYMBOL_MAP[s].startswith('^F')]),
            'commodities': len([s for s in YAHOO_SYMBOL_MAP if YAHOO_SYMBOL_MAP[s].endswith('=F')]),
            'indices': len([s for s in YAHOO_SYMBOL_MAP if YAHOO_SYMBOL_MAP[s].startswith('^') and not YAHOO_SYMBOL_MAP[s].startswith('^T') and not YAHOO_SYMBOL_MAP[s].startswith('^I') and not YAHOO_SYMBOL_MAP[s].startswith('^F')]),
        }
    }


def clear_cache(symbol: str = None):
    """Clear Yahoo data cache. If symbol is given, clear only that symbol."""
    if symbol:
        _yahoo_cache.pop(symbol, None)
    else:
        _yahoo_cache.clear()
