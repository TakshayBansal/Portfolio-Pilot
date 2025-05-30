import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import numpy as np
import sys
import os
import math # Added for math.nan and float('inf')

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

    @patch('services.suggestions_services.optimize_stock_allocation')
    @patch('services.suggestions_services.optimize_portfolio')
    @patch('services.suggestions_services.load_data')
    @patch('services.suggestions_services.get_top_50_stock_tickers')
    @patch('services.suggestions_services.np.dot') # To control expected_return, volatility
    @patch('services.suggestions_services.np.sqrt') # To control volatility
    def test_get_optimized_portfolio_with_non_compliant_values(self,
                                             mock_np_sqrt,
                                             mock_np_dot,
                                             mock_get_top_50, 
                                             mock_load_data, 
                                             mock_optimize_portfolio,
                                             mock_optimize_stock_allocation):
        print("Testing Suggestion Service: Non-compliant values sanitization")

        # --- Mock Basic Setup ---
        mock_tickers = ["MOCK1", "MOCK2", "MOCK3"]
        mock_get_top_50.return_value = mock_tickers
        
        # Mock load_data to return some valid basic data
        mock_general_asset_data = self.create_mock_close_data([100, 101, 102, 103, 104])
        mock_stock_specific_data = self.create_mock_close_data([10,11,12])
        
        def load_data_side_effect(asset_type_or_ticker):
            if asset_type_or_ticker in ["stocks", "bonds", "real_estate", "commodities"]:
                return mock_general_asset_data
            else: # For MOCK1, MOCK2, MOCK3
                df = self.create_mock_close_data([10,11,12])
                df['Ticker'] = asset_type_or_ticker
                return df
        mock_load_data.side_effect = load_data_side_effect

        investment_amount = 100000

        # --- Scenario 1: Non-compliant values from optimize_portfolio ---
        # optimize_portfolio returns weights like [60.0, np.nan, 10.0, np.inf]
        # These are percentages.
        mock_optimize_portfolio.return_value = np.array([60.0, np.nan, 10.0, np.inf])
        
        # optimize_stock_allocation returns compliant values for this part of the test
        mock_optimize_stock_allocation.return_value = {"MOCK1": 100.0} 

        # Mock np.dot and np.sqrt to return valid numbers for portfolio_metrics
        # to isolate the effect of optimize_portfolio's output
        mock_np_dot.side_effect = lambda x, y: 0.05 if len(x)==4 else 0.01 # crude differentiation for different calls
        mock_np_sqrt.return_value = 0.1 

        result1 = get_optimized_portfolio(investment=investment_amount, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        
        self.assertNotIn("error", result1)
        self.assertEqual(result1["optimized_allocation"]['Stocks'], 60.0)
        self.assertIsNone(result1["optimized_allocation"]['Bonds']) # from np.nan
        self.assertEqual(result1["optimized_allocation"]['Real_Estate'], 10.0)
        self.assertIsNone(result1["optimized_allocation"]['Commodities']) # from np.inf

        self.assertEqual(result1["investment_breakdown"]['Stocks'], 60000.0)
        self.assertIsNone(result1["investment_breakdown"]['Bonds'])
        self.assertEqual(result1["investment_breakdown"]['Real_Estate'], 10000.0)
        self.assertIsNone(result1["investment_breakdown"]['Commodities'])
        
        # --- Scenario 2: Non-compliant values from optimize_stock_allocation ---
        mock_optimize_portfolio.return_value = np.array([50.0, 25.0, 15.0, 10.0]) # Valid weights
        mock_optimize_stock_allocation.return_value = {"MOCK1": np.inf, "MOCK2": 50.0, "MOCK3": np.nan}

        result2 = get_optimized_portfolio(investment=investment_amount, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        
        self.assertNotIn("error", result2)
        self.assertIsNone(result2["optimized_stock_allocation"]["MOCK1"])
        self.assertEqual(result2["optimized_stock_allocation"]["MOCK2"], 50.0)
        self.assertIsNone(result2["optimized_stock_allocation"]["MOCK3"])

        stock_investment_total = result2["investment_breakdown"]['Stocks'] # 50000
        self.assertIsNone(result2["stock_allocation_investment"]["MOCK1"])
        self.assertEqual(result2["stock_allocation_investment"]["MOCK2"], round(0.50 * stock_investment_total, 2))
        self.assertIsNone(result2["stock_allocation_investment"]["MOCK3"])

        # --- Scenario 3: Non-compliant values for portfolio_metrics (direct mock via np.dot/sqrt) ---
        mock_optimize_portfolio.return_value = np.array([60.0, 20.0, 10.0, 10.0]) # Valid weights
        mock_optimize_stock_allocation.return_value = {"MOCK1": 100.0} # Valid stock alloc

        # Mock np.dot and np.sqrt to produce inf/nan for portfolio metrics calculations
        # This is a bit indirect. The actual values are:
        # expected_return = np.dot(returns.mean(), optimized_weights) *252*  100
        # volatility = np.sqrt(np.dot(optimized_weights.T, np.dot(cov_matrix, optimized_weights))) * np.sqrt(252) * 100
        # sharpe_ratio = (expected_return - risk_free_rate / 100) / volatility if volatility > 0 else 0

        # Let's make expected_return_raw (before *252*100) become inf
        # and volatility_raw (before *sqrt(252)*100) become nan
        
        # Mocking np.dot to return specific values based on its usage context (hard to do robustly)
        # A more stable approach would be to patch 'expected_return = ...', 'volatility = ...' lines
        # directly if the tool allowed patching variables in scope, but it doesn't.
        # So, we use a side_effect on np.dot that returns inf for the first relevant call (for expected_return)
        # and make np.sqrt return nan for the volatility calculation.
        
        # This part is tricky because np.dot is used multiple times.
        # We rely on the order of operations.
        # 1. np.dot(returns.mean(), optimized_weights) for expected_return
        # 2. np.dot(optimized_weights.T, np.dot(cov_matrix, optimized_weights)) for volatility
        
        # For simplicity, we'll assume the first call to np.dot (with 1-D array and weights) is for expected_return
        # and the more complex one for volatility's dot product.
        # This is fragile. Ideally, patch the variables directly if tool supported.

        # Resetting side effect for more granular control
        def dot_side_effect_for_metrics(*args):
            if len(args[0].shape) == 1 and len(args[1].shape) == 1: # Potentially returns.mean() and optimized_weights
                return float('inf') # For expected_return calculation
            return 0.01 # Default for other np.dot calls like in volatility
        mock_np_dot.side_effect = dot_side_effect_for_metrics
        mock_np_sqrt.side_effect = lambda x: math.nan if x == 0.01 else 0.1 # Make volatility nan

        result3 = get_optimized_portfolio(investment=investment_amount, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        
        self.assertNotIn("error", result3)
        self.assertIsNone(result3["portfolio_metrics"]["Expected Return (%)"])
        self.assertIsNone(result3["portfolio_metrics"]["Risk (Volatility %)"])
        self.assertIsNone(result3["portfolio_metrics"]["Sharpe Ratio"]) # Will be None as volatility is None

        # Test case: Sharpe Ratio is None due to zero volatility
        mock_np_dot.side_effect = lambda x,y : 0.05 # valid return
        mock_np_sqrt.side_effect = lambda x: 0.0 # Make volatility zero

        result4 = get_optimized_portfolio(investment=investment_amount, duration=5, user_allocation=[.25]*4, risk_tolerance=0.5)
        self.assertNotIn("error", result4)
        self.assertIsNotNone(result4["portfolio_metrics"]["Expected Return (%)"]) # Should be a number
        self.assertEqual(result4["portfolio_metrics"]["Risk (Volatility %)"], 0.0) # Zero volatility
        self.assertIsNone(result4["portfolio_metrics"]["Sharpe Ratio"]) # Sharpe should be None
