import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Get the absolute path of the Backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")  # Ensure this points to the correct folder

# In-memory cache for stock data
stock_data_cache = {}

def load_data(asset_type):
    """
    Loads historical data for the given asset type or individual stock ticker.
    For "bonds", "real_estate", "commodities", data is loaded from CSV files.
    For individual stock tickers (e.g., "AAPL"), data is fetched using yfinance
    and cached in memory for the current day.
    """
    
    # Define paths for non-stock asset types
    other_asset_file_paths = {
        "bonds": os.path.join(DATA_DIR, "bond_data_5y - Copy.csv"),
        "real_estate": os.path.join(DATA_DIR, "real_estate_data_5y - Copy.csv"),
        "commodities": os.path.join(DATA_DIR, "commodity_data_5y - Copy.csv")
    }

    if asset_type in other_asset_file_paths:
        file_path = other_asset_file_paths[asset_type]
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"❌ Data file not found: {file_path}")
        print(f"📂 Loading data from: {file_path}")
        return pd.read_csv(file_path)

    # Handle "stocks" asset type specifically for ^GSPC data
    elif asset_type == "stocks":
        ticker_symbol = "^GSPC" # Use ^GSPC as the general stock market representation
        print(f"ℹ️ Asset type 'stocks' requested, fetching data for {ticker_symbol}")
        # Check cache first for ^GSPC
        if ticker_symbol in stock_data_cache:
            cached_data, fetch_date = stock_data_cache[ticker_symbol]
            if fetch_date == datetime.today().date():
                print(f"✅ Using cached data for {ticker_symbol} (representing 'stocks')")
                return cached_data.copy()
        
        # If not in cache or stale, fetch ^GSPC from yfinance
        print(f"⬇️ Fetching data for {ticker_symbol} (representing 'stocks') from yfinance...")
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            data = ticker_obj.history(period="5y")
            if data.empty:
                raise ValueError(f"❌ No data found for {ticker_symbol} (representing 'stocks').")
            if 'Close' not in data.columns:
                raise ValueError(f"❌ 'Close' price not available for {ticker_symbol} (representing 'stocks')")
            data['Ticker'] = ticker_symbol # Add Ticker column for consistency, though it's ^GSPC
            stock_data_cache[ticker_symbol] = (data.copy(), datetime.today().date())
            return data
        except Exception as e:
            raise ValueError(f"❌ Error fetching data for {ticker_symbol} (representing 'stocks') from yfinance: {e}")

    # Handle individual stock tickers using yfinance and caching
    else:
        # Check cache first
        if asset_type in stock_data_cache:
            cached_data, fetch_date = stock_data_cache[asset_type]
            # Check if cache is from today
            if fetch_date == datetime.today().date():
                print(f"✅ Using cached data for {asset_type}")
                # Return a copy to prevent modification of cached DataFrame
                return cached_data.copy()

        # If not in cache or stale, fetch from yfinance
        print(f"⬇️ Fetching data for {asset_type} from yfinance...")
        try:
            ticker_obj = yf.Ticker(asset_type)
            # Fetch 5 years of historical data
            data = ticker_obj.history(period="5y") 
            
            if data.empty:
                raise ValueError(f"❌ No data found for stock ticker: {asset_type}. It might be delisted or an invalid ticker.")
            
            # Ensure 'Close' price is available
            if 'Close' not in data.columns:
                raise ValueError(f"❌ 'Close' price not available for {asset_type}")

            # Add 'Ticker' column
            data['Ticker'] = asset_type
            
            # Cache the fetched data with the current date
            stock_data_cache[asset_type] = (data.copy(), datetime.today().date()) # Store a copy
            
            return data # Return the original fetched data, not the copy from cache at this point
        except Exception as e:
            # Broad exception for yfinance issues (e.g., network, invalid ticker)
            raise ValueError(f"❌ Error fetching data for {asset_type} from yfinance: {e}")


def get_top_50_stock_tickers() -> list[str]:
    """
    Returns a fixed list of 50 well-known stock tickers.
    """
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "BRK-A", "JPM", 
        "JNJ", "V", "PG", "UNH", "HD", "MA", "BAC", "DIS", "PYPL", "NFLX", 
        "ADBE", "CRM", "XOM", "CSCO", "PEP", "KO", "T", "INTC", "CMCSA", 
        "VZ", "PFE", "MRK", "WMT", "CVX", "ABT", "LLY", "ORCL", "DHR", 
        "ACN", "QCOM", "C", "IBM", "AMGN", "HON", "UTX", "SBUX", "CAT", 
        "GS", "MMM", "BA", "GE", "NKE"
    ]
