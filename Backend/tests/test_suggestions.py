import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import numpy as np
import sys
import os

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.suggestions_services import get_optimized_portfolio

class TestSuggestionsService(unittest.TestCase):

    def create_mock_close_data(self, prices):
        return pd.DataFrame({'Close': prices})

    @patch('services.suggestions_services.optimize_stock_allocation')
    @patch('services.suggestions_services.optimize_portfolio')
    @patch('services.suggestions_services.load_data')
    @patch('services.suggestions_services.get_top_50_stock_tickers')
    def test_get_optimized_portfolio_success(self, 
                                             mock_get_top_50, 
                                             mock_load_data, 
                                             mock_optimize_portfolio,
                                             mock_optimize_stock_allocation):
        
        print("Testing Suggestion Service: get_optimized_portfolio")

        # --- Mock Setup ---
        mock_tickers = ["MOCK1", "MOCK2"]
        mock_get_top_50.return_value = mock_tickers

        # Mock load_data behavior
        mock_stock_general_data = self.create_mock_close_data([100, 101, 102]) # For general 'Stocks' asset category
        mock_bond_data = self.create_mock_close_data([50, 50.1, 50.2])
        mock_real_estate_data = self.create_mock_close_data([200, 201, 200])
        mock_commodity_data = self.create_mock_close_data([30, 30.5, 31])
        
        mock_stock_detail_data_m1 = self.create_mock_close_data([10, 11, 12])
        mock_stock_detail_data_m1['Ticker'] = "MOCK1"
        mock_stock_detail_data_m2 = self.create_mock_close_data([20, 21, 22])
        mock_stock_detail_data_m2['Ticker'] = "MOCK2"

        def load_data_side_effect(asset_type_or_ticker):
            if asset_type_or_ticker == "stocks": # General SPY data
                return mock_stock_general_data
            elif asset_type_or_ticker == "bonds":
                return mock_bond_data
            elif asset_type_or_ticker == "real_estate":
                return mock_real_estate_data
            elif asset_type_or_ticker == "commodities":
                return mock_commodity_data
            elif asset_type_or_ticker == "MOCK1":
                return mock_stock_detail_data_m1
            elif asset_type_or_ticker == "MOCK2":
                return mock_stock_detail_data_m2
            return pd.DataFrame() # Default empty
            
        mock_load_data.side_effect = load_data_side_effect

        # Mock optimize_portfolio (overall asset classes)
        # Returns weights in percentage, e.g., [60, 20, 10, 10] for Stocks, Bonds, RE, Commodities
        mock_optimized_portfolio_weights = np.array([60.0, 20.0, 10.0, 10.0]) 
        mock_optimize_portfolio.return_value = mock_optimized_portfolio_weights
        
        # Mock optimize_stock_allocation (individual stocks)
        # Returns dict, e.g., {"MOCK1": 70.0, "MOCK2": 30.0}
        mock_stock_alloc = {"MOCK1": 70.00, "MOCK2": 30.00}
        mock_optimize_stock_allocation.return_value = mock_stock_alloc

        # --- Call the function ---
        investment_amount = 100000
        user_allocation_input = [0.25, 0.25, 0.25, 0.25] # Example, actual effect depends on mock_optimize_portfolio
        
        result = get_optimized_portfolio(
            investment=investment_amount,
            duration=5, # years
            user_allocation=user_allocation_input,
            risk_tolerance=0.6 # Example
        )

        # --- Assertions ---
        self.assertNotIn("error", result, f"Optimization returned an error: {result.get('error')}")

        # Assert mocks were called
        mock_get_top_50.assert_called_once()
        
        # Expected load_data calls: 4 general assets + 2 specific stocks
        expected_load_calls = [
            call("stocks"), call("bonds"), call("real_estate"), call("commodities"),
            call("MOCK1"), call("MOCK2")
        ]
        mock_load_data.assert_has_calls(expected_load_calls, any_order=True) # any_order due to dict iteration for MOCK1/2
        self.assertEqual(mock_load_data.call_count, 6)


        mock_optimize_portfolio.assert_called_once()
        # First arg to optimize_portfolio is 'data', a DataFrame. We check its columns.
        pd_call_args = mock_optimize_portfolio.call_args[0][0]
        self.assertListEqual(list(pd_call_args.columns), ['Stocks', 'Bonds', 'Real_Estate', 'Commodities'])

        mock_optimize_stock_allocation.assert_called_once()
        # First arg to optimize_stock_allocation is 'stock_data' dict
        osa_call_args_stock_data = mock_optimize_stock_allocation.call_args[0][0]
        self.assertIn("MOCK1", osa_call_args_stock_data)
        self.assertIn("MOCK2", osa_call_args_stock_data)
        pd.testing.assert_frame_equal(osa_call_args_stock_data["MOCK1"], mock_stock_detail_data_m1)

        # Check results structure and some values
        self.assertIn("optimized_allocation", result)
        self.assertIn("investment_breakdown", result)
        self.assertIn("optimized_stock_allocation", result)
        self.assertIn("stock_allocation_investment", result)
        self.assertIn("portfolio_metrics", result)

        # Check optimized_allocation based on mock_optimize_portfolio
        expected_overall_alloc = {
            'Stocks': 60.0, 'Bonds': 20.0, 'Real_Estate': 10.0, 'Commodities': 10.0
        }
        self.assertEqual(result["optimized_allocation"], expected_overall_alloc)

        # Check investment_breakdown
        expected_inv_breakdown = {
            'Stocks': 0.60 * investment_amount,
            'Bonds': 0.20 * investment_amount,
            'Real_Estate': 0.10 * investment_amount,
            'Commodities': 0.10 * investment_amount
        }
        self.assertEqual(result["investment_breakdown"], expected_inv_breakdown)

        # Check optimized_stock_allocation from mock
        self.assertEqual(result["optimized_stock_allocation"], mock_stock_alloc)

        # Check stock_allocation_investment
        stock_investment_total = expected_inv_breakdown['Stocks']
        expected_stock_inv = {
            "MOCK1": round((mock_stock_alloc["MOCK1"] / 100) * stock_investment_total, 2),
            "MOCK2": round((mock_stock_alloc["MOCK2"] / 100) * stock_investment_total, 2)
        }
        self.assertEqual(result["stock_allocation_investment"], expected_stock_inv)
        
        self.assertIn("Expected Return (%)", result["portfolio_metrics"]) # Calculation involves many factors, just check presence

    @patch('services.suggestions_services.load_data')
    @patch('services.suggestions_services.get_top_50_stock_tickers')
    def test_get_optimized_portfolio_stock_data_load_fail(self, mock_get_top_50, mock_load_data):
        mock_get_top_50.return_value = ["MOCK1", "MOCK2"]
        
        # General assets load fine
        mock_load_data.side_effect = lambda asset: self.create_mock_close_data([1,2]) if asset in ["stocks", "bonds", "real_estate", "commodities"] else (_ for _ in ()).throw(ValueError(f"Failed to load {asset}"))

        result = get_optimized_portfolio(investment=10000, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        # Should still proceed if general asset classes load, but stock_data for optimization will be empty
        # The service function has a check: if not stock_data: return {"error": ...}
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Could not load data for any stock tickers. Portfolio optimization aborted.")


    @patch('services.suggestions_services.optimize_stock_allocation')
    @patch('services.suggestions_services.optimize_portfolio')
    @patch('services.suggestions_services.load_data')
    @patch('services.suggestions_services.get_top_50_stock_tickers')
    def test_get_optimized_portfolio_stock_opt_fail(self, mock_get_top_50, mock_load_data, mock_optimize_portfolio, mock_optimize_stock_allocation):
        mock_get_top_50.return_value = ["MOCK1"]
        mock_load_data.return_value = self.create_mock_close_data([1,2]) # Generic mock data for all calls
        mock_optimize_portfolio.return_value = np.array([100.0, 0, 0, 0]) # All in stocks
        mock_optimize_stock_allocation.return_value = {"error": "Stock allocation optimization failed."}

        result = get_optimized_portfolio(investment=10000, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Stock allocation optimization failed.")


if __name__ == '__main__':
    unittest.main()
