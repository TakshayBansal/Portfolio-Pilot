import os
import pandas as pd


# Get the absolute path of the Backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")  # Ensure this points to the correct folder

def load_data(asset_type):
    """
    Loads historical data for the given asset type or individual stock ticker.
    If asset_type is a stock ticker, extracts only its data from stock_data_5y.csv.
    """
 
    file_paths = {
        "stocks": os.path.join(DATA_DIR, "stock_data_5y.csv"),
        "bonds": os.path.join(DATA_DIR, "bond_data_5y - Copy.csv"),
        "real_estate": os.path.join(DATA_DIR, "real_estate_data_5y - Copy.csv"),
        "commodities": os.path.join(DATA_DIR, "commodity_data_5y - Copy.csv")
    }

  
    if asset_type in file_paths:
        file_path = file_paths[asset_type]

    elif asset_type in ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]:  
        stock_file = file_paths["stocks"]  

        if not os.path.exists(stock_file):
            raise FileNotFoundError(f"❌ Stock data file not found: {stock_file}")

<<<<<<< Updated upstream
        
        df = pd.read_csv(stock_file)

        if "Ticker" not in df.columns:
            raise ValueError("❌ Missing 'Ticker' column in stock data file.")

      
        stock_data = df[df["Ticker"] == asset_type]

        if stock_data.empty:
            raise ValueError(f"❌ No data found for stock: {asset_type}")

        return stock_data.reset_index(drop=True)
=======
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
>>>>>>> Stashed changes

    else:
        raise ValueError(f"❌ Invalid asset type: {asset_type}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ Data file not found: {file_path}")

    print(f"📂 Loading data from: {file_path}")  
    return pd.read_csv(file_path)
