import pandas as pd
from .data_loader import load_data

def get_market_trend(ticker: str = '^GSPC', short_window: int = 50, long_window: int = 200) -> str:
    """
    Determines the market trend based on short-term and long-term moving averages.

    Args:
        ticker (str): The ticker symbol for the market index (default '^GSPC').
        short_window (int): The window size for the short-term moving average.
        long_window (int): The window size for the long-term moving average.

    Returns:
        str: "bull", "bear", or "neutral" indicating the market trend.
    """
    try:
        data = load_data(ticker)

        if 'Close' not in data.columns:
            print(f"⚠️ Warning: 'Close' column not found for ticker {ticker}. Returning 'neutral' trend.")
            return "neutral"

        if len(data) < long_window:
            print(f"⚠️ Warning: Insufficient data for {ticker} to calculate {long_window}-day MA (got {len(data)} days). Returning 'neutral' trend.")
            return "neutral"

        # Calculate short-term moving average (SMA)
        data['SMA'] = data['Close'].rolling(window=short_window).mean()
        
        # Calculate long-term moving average (LMA)
        data['LMA'] = data['Close'].rolling(window=long_window).mean()

        # Get the most recent values
        latest_sma = data['SMA'].iloc[-1]
        latest_lma = data['LMA'].iloc[-1]

        if pd.isna(latest_sma) or pd.isna(latest_lma):
            print(f"⚠️ Warning: Could not calculate moving averages for {ticker} (possibly due to insufficient recent data after rolling mean). Returning 'neutral' trend.")
            return "neutral"

        if latest_sma > latest_lma:
            return "bull"
        else:
            return "bear"
            
    except FileNotFoundError:
        print(f"⚠️ Warning: Data file not found for ticker {ticker} in load_data. Returning 'neutral' trend.")
        return "neutral"
    except ValueError as ve: # Catching specific errors from load_data or data checks
        print(f"⚠️ Warning: ValueError encountered for ticker {ticker}: {ve}. Returning 'neutral' trend.")
        return "neutral"
    except Exception as e:
        print(f"❌ Error determining market trend for {ticker}: {e}. Returning 'neutral' trend.")
        return "neutral"

if __name__ == '__main__':
    # Example usage:
    # Ensure yfinance is installed and data_loader can fetch ^GSPC.
    # This part is for testing and might require running from the project root or adjusting paths.
    try:
        # Adjust the import path if running this script directly for testing
        # from data_loader import load_data 
        print(f"Current market trend for ^GSPC: {get_market_trend('^GSPC')}")
        print(f"Current market trend for AAPL: {get_market_trend('AAPL')}") # Example with another ticker
        # Test with a ticker that might have less data or issues
        # print(f"Current market trend for NONEXISTENT_TICKER: {get_market_trend('NONEXISTENT_TICKER')}")
    except ImportError:
        print("Could not run example usage due to ImportError (likely .data_loader issue when run standalone).")
    except Exception as e:
        print(f"An error occurred during example usage: {e}")
