import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.market_trend import get_market_trend

class TestMarketTrend(unittest.TestCase):

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_bull(self, mock_load_data):
        # Create a DataFrame where SMA > LMA
        data = {'Close': [i for i in range(1, 201)]} # Increasing prices
        mock_df = pd.DataFrame(data)
        # Simple way to make SMA > LMA for recent values: make last 50 values significantly higher
        mock_df['Close'].iloc[-50:] = [i * 2 for i in mock_df['Close'].iloc[-50:]]
        
        mock_load_data.return_value = mock_df
        
        trend = get_market_trend(ticker='TEST_BULL')
        self.assertEqual(trend, "bull")
        mock_load_data.assert_called_once_with('TEST_BULL')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_bear(self, mock_load_data):
        # Create a DataFrame where SMA < LMA
        data = {'Close': [200 - i for i in range(1, 201)]} # Decreasing prices
        mock_df = pd.DataFrame(data)
        # Simple way to make SMA < LMA for recent values: make last 50 values significantly lower
        mock_df['Close'].iloc[-50:] = [i / 2 for i in mock_df['Close'].iloc[-50:]]

        mock_load_data.return_value = mock_df
        
        trend = get_market_trend(ticker='TEST_BEAR')
        self.assertEqual(trend, "bear")
        mock_load_data.assert_called_once_with('TEST_BEAR')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_neutral_insufficient_data(self, mock_load_data):
        # DataFrame with less than long_window (200) rows
        mock_df = pd.DataFrame({'Close': [i for i in range(1, 199)]}) # 198 rows
        mock_load_data.return_value = mock_df
        
        trend = get_market_trend(ticker='TEST_INSUFFICIENT')
        self.assertEqual(trend, "neutral")
        mock_load_data.assert_called_once_with('TEST_INSUFFICIENT')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_neutral_load_data_exception(self, mock_load_data):
        mock_load_data.side_effect = FileNotFoundError("Mocked file not found")
        
        trend = get_market_trend(ticker='TEST_LOAD_FAIL')
        self.assertEqual(trend, "neutral")
        mock_load_data.assert_called_once_with('TEST_LOAD_FAIL')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_neutral_load_data_value_error(self, mock_load_data):
        mock_load_data.side_effect = ValueError("Mocked value error")
        
        trend = get_market_trend(ticker='TEST_LOAD_VAL_ERR')
        self.assertEqual(trend, "neutral")
        mock_load_data.assert_called_once_with('TEST_LOAD_VAL_ERR')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_neutral_no_close_column(self, mock_load_data):
        mock_df = pd.DataFrame({'Open': [i for i in range(1, 201)]}) # No 'Close' column
        mock_load_data.return_value = mock_df
        
        trend = get_market_trend(ticker='TEST_NO_CLOSE')
        self.assertEqual(trend, "neutral")
        mock_load_data.assert_called_once_with('TEST_NO_CLOSE')

    @patch('utils.market_trend.load_data')
    def test_get_market_trend_neutral_sma_lma_nan(self, mock_load_data):
        # Create a DataFrame that might result in NaN for MAs if not enough distinct periods
        # e.g. all same prices, or not enough data points for the rolling window
        # For this test, we'll use a smaller frame that will certainly be less than short_window after some NaNs
        mock_df = pd.DataFrame({'Close': [100] * 40}) # Only 40 data points, short_window is 50
        mock_load_data.return_value = mock_df
        
        trend = get_market_trend(ticker='TEST_NAN_MA')
        self.assertEqual(trend, "neutral") # Should be neutral as SMA will be NaN
        mock_load_data.assert_called_once_with('TEST_NAN_MA')

if __name__ == '__main__':
    unittest.main()
