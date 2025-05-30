import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
from datetime import datetime, date
import sys
import os

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_loader import load_data, get_top_50_stock_tickers, stock_data_cache

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # Clear the cache before each test
        stock_data_cache.clear()

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_success(self, mock_yfinance_ticker):
        # Mock yf.Ticker().history()
        mock_history = MagicMock()
        mock_df = pd.DataFrame({'Close': [100, 101, 102]})
        mock_history.return_value = mock_df
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        ticker = 'AAPL'
        data = load_data(ticker)

        self.assertIsInstance(data, pd.DataFrame)
        self.assertIn('Close', data.columns)
        self.assertIn('Ticker', data.columns)
        self.assertEqual(data['Ticker'].iloc[0], ticker)
        mock_yfinance_ticker.assert_called_once_with(ticker)
        mock_ticker_instance.history.assert_called_once_with(period="5y")

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_spy_for_stocks_asset_type(self, mock_yfinance_ticker):
        mock_history = MagicMock()
        mock_df = pd.DataFrame({'Close': [200, 201, 202]})
        mock_history.return_value = mock_df
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        asset_type = 'stocks' # This should trigger SPY fetching
        spy_ticker_symbol = "^GSPC"
        data = load_data(asset_type)

        self.assertIsInstance(data, pd.DataFrame)
        self.assertIn('Close', data.columns)
        self.assertIn('Ticker', data.columns)
        self.assertEqual(data['Ticker'].iloc[0], spy_ticker_symbol)
        mock_yfinance_ticker.assert_called_once_with(spy_ticker_symbol)
        mock_ticker_instance.history.assert_called_once_with(period="5y")

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_empty_dataframe(self, mock_yfinance_ticker):
        mock_history = MagicMock()
        mock_history.return_value = pd.DataFrame() # Empty DataFrame
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        ticker = 'EMPTYTICKER'
        with self.assertRaisesRegex(ValueError, f"❌ No data found for stock ticker: {ticker}"):
            load_data(ticker)

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_yfinance_api_error(self, mock_yfinance_ticker):
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history.side_effect = Exception("API network error")
        mock_yfinance_ticker.return_value = mock_ticker_instance
        
        ticker = 'ERRORTICKER'
        with self.assertRaisesRegex(ValueError, f"❌ Error fetching data for {ticker} from yfinance: API network error"):
            load_data(ticker)

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_caching(self, mock_yfinance_ticker):
        mock_history = MagicMock()
        mock_df = pd.DataFrame({'Close': [100, 101, 102]})
        mock_history.return_value = mock_df
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        ticker = 'TESTCACHE'
        
        # First call - should call yf.Ticker and cache
        data1 = load_data(ticker)
        self.assertIn(ticker, stock_data_cache)
        mock_yfinance_ticker.assert_called_once_with(ticker)
        mock_ticker_instance.history.assert_called_once_with(period="5y")
        
        # Reset mocks for the second call check
        mock_yfinance_ticker.reset_mock()
        mock_ticker_instance.history.reset_mock()

        # Second call - should use cache
        data2 = load_data(ticker)
        
        mock_yfinance_ticker.assert_not_called() # yf.Ticker should not be called again
        mock_ticker_instance.history.assert_not_called() # .history() should not be called again
        pd.testing.assert_frame_equal(data1, data2)

    @patch('utils.data_loader.yf.Ticker')
    def test_load_data_cache_stale(self, mock_yfinance_ticker):
        mock_history = MagicMock()
        mock_df = pd.DataFrame({'Close': [100, 101, 102]})
        mock_history.return_value = mock_df
        
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.history = mock_history
        mock_yfinance_ticker.return_value = mock_ticker_instance

        ticker = 'STALETEST'
        
        # Simulate data cached yesterday
        yesterday = date.today() - pd.Timedelta(days=1)
        stock_data_cache[ticker] = (mock_df.copy(), yesterday)

        # First call - should find stale data and fetch again
        data1 = load_data(ticker)
        mock_yfinance_ticker.assert_called_once_with(ticker) # Should be called as cache is stale
        mock_ticker_instance.history.assert_called_once_with(period="5y")
        
        # Verify cache is updated
        self.assertEqual(stock_data_cache[ticker][1], date.today())


    def test_get_top_50_stock_tickers(self):
        tickers = get_top_50_stock_tickers()
        self.assertIsInstance(tickers, list)
        self.assertEqual(len(tickers), 50)
        self.assertEqual(len(set(tickers)), 50, "Tickers should be unique")
        for ticker in tickers:
            self.assertIsInstance(ticker, str)

    @patch('utils.data_loader.os.path.exists')
    @patch('utils.data_loader.pd.read_csv')
    def test_load_data_other_assets(self, mock_read_csv, mock_path_exists):
        mock_path_exists.return_value = True
        mock_df = pd.DataFrame({'Close': [10, 11, 12]})
        mock_read_csv.return_value = mock_df

        asset_type = "bonds"
        data = load_data(asset_type)
        
        self.assertIsInstance(data, pd.DataFrame)
        mock_read_csv.assert_called_once()
        # We don't check specific path here, just that read_csv was called
        # as path construction can be tricky to mock perfectly.

    @patch('utils.data_loader.os.path.exists')
    def test_load_data_other_assets_file_not_found(self, mock_path_exists):
        mock_path_exists.return_value = False
        asset_type = "commodities"
        with self.assertRaises(FileNotFoundError):
            load_data(asset_type)

if __name__ == '__main__':
    unittest.main()
