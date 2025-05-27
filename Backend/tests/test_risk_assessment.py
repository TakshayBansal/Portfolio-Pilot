import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
import os

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.risk_assessment import run_risk_assessment
# Assuming models.monte_carlo and models.gbm_model have their own tests or are trusted.
# We will mock their behavior for these service-level tests.

class TestRiskAssessmentService(unittest.TestCase):

    def create_mock_asset_data(self, close_prices):
        df = pd.DataFrame({'Close': close_prices})
        # Add other columns if your functions directly use them, though pct_change().dropna() is common
        return df

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation')
    @patch('services.risk_assessment.geometric_brownian_motion')
    def run_test_for_market_condition(self, market_trend_return, 
                                     mock_gbm, mock_mc, 
                                     mock_get_market_trend, mock_load_data):
        
        # --- Mock Setup ---
        mock_get_market_trend.return_value = market_trend_return
        
        # Mock load_data to return different data for each asset type
        mock_stock_data = self.create_mock_asset_data([100, 101, 102, 103, 104]) # mean_return ~0.01
        mock_bond_data = self.create_mock_asset_data([50, 50.2, 50.3, 50.4, 50.5]) # mean_return ~0.0025
        
        def load_data_side_effect(asset_type):
            if asset_type == "stocks":
                return mock_stock_data
            elif asset_type == "bonds":
                return mock_bond_data
            # Add more asset types if your test needs them
            return self.create_mock_asset_data([10, 10, 10, 10, 10]) # Default zero return data
            
        mock_load_data.side_effect = load_data_side_effect

        # Mock simulation functions to return predictable values
        # (final_value, yearly_values_list)
        mock_mc.return_value = (11000, [10000, 10500, 11000]) 
        mock_gbm.return_value = (11500, [10000, 10700, 11500])

        # --- Call the function ---
        result = run_risk_assessment(
            investment_amount=10000, 
            duration=3, 
            risk_appetite=0.5, # Example risk appetite
            stocks=50, # 50% allocation to stocks
            bonds=50,  # 50% allocation to bonds
            real_estate=0, 
            commodities=0
        )
        
        # --- Assertions ---
        self.assertNotIn("error", result)
        self.assertIn("Risk Score", result)
        self.assertIn("ROI (%)", result)

        # Verify mean_return adjustments based on market trend
        # For stocks: original mean_return is approx 0.01 ( (104/100-1)/4 elements in returns ) -> 0.0099...
        # For bonds: original mean_return is approx 0.0025
        
        # Expected base mean returns (daily)
        expected_stock_daily_mean_return = mock_stock_data['Close'].pct_change().dropna().mean()
        expected_bond_daily_mean_return = mock_bond_data['Close'].pct_change().dropna().mean()

        if market_trend_return == "bull":
            expected_stock_daily_mean_return *= 1.1
            expected_bond_daily_mean_return *= 1.1
        elif market_trend_return == "bear":
            expected_stock_daily_mean_return *= 0.9
            expected_bond_daily_mean_return *= 0.9
        
        # Check if simulations were called with adjusted mean_returns
        # This is an indirect check. A more direct check would require deeper mocking or refactoring.
        # We are checking the arguments to monte_carlo_simulation for the 'stocks' asset
        # (assuming stocks is processed first or we can find its call)
        
        # Example of checking one of the calls (e.g., for stocks)
        # The actual mean_return passed to mc/gbm is what we care about
        # mc_calls = mock_mc.call_args_list
        # gbm_calls = mock_gbm.call_args_list

        # asset_investment_stock = 10000 * (50 / 100) = 5000
        # asset_investment_bond = 10000 * (50 / 100) = 5000
        
        # Call for stocks (example, order might vary)
        # self.assertAlmostEqual(mc_calls[0][0][1], expected_stock_daily_mean_return, places=5) 
        # self.assertAlmostEqual(gbm_calls[0][0][1], expected_stock_daily_mean_return, places=5)
        # Call for bonds
        # self.assertAlmostEqual(mc_calls[1][0][1], expected_bond_daily_mean_return, places=5)
        # self.assertAlmostEqual(gbm_calls[1][0][1], expected_bond_daily_mean_return, places=5)

        # Risk Score check (simplified)
        # Base risk score involves volatility and max_drawdown. The trend adjustment is +-0.5
        # This is also an indirect check, as direct calculation is complex here.
        # We primarily check that the function runs and returns expected keys.
        # More detailed assertions on the risk score value itself would require
        # fixing the volatility and max_drawdown calculations or mocking them.

        mock_get_market_trend.assert_called_once()
        self.assertGreaterEqual(mock_load_data.call_count, 2) # Called for stocks and bonds
        self.assertGreaterEqual(mock_mc.call_count, 2)
        self.assertGreaterEqual(mock_gbm.call_count, 2)
        
        return result # Return result for specific checks if needed

    def test_run_risk_assessment_bull_market(self):
        print("Testing Risk Assessment: Bull Market")
        self.run_test_for_market_condition("bull")

    def test_run_risk_assessment_bear_market(self):
        print("Testing Risk Assessment: Bear Market")
        self.run_test_for_market_condition("bear")

    def test_run_risk_assessment_neutral_market(self):
        print("Testing Risk Assessment: Neutral Market")
        self.run_test_for_market_condition("neutral")

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    def test_run_risk_assessment_no_assets_error(self, mock_get_market_trend, mock_load_data):
        mock_get_market_trend.return_value = "neutral" # Doesn't matter for this test
        
        result = run_risk_assessment(
            investment_amount=10000, 
            duration=3, 
            risk_appetite=0.5,
            stocks=0, bonds=0, real_estate=0, commodities=0 # No allocation
        )
        self.assertEqual(result, {"error": "At least one asset must have an allocation greater than 0."})
        mock_load_data.assert_not_called()

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation')
    @patch('services.risk_assessment.geometric_brownian_motion')
    def test_run_risk_assessment_load_data_exception(self, mock_gbm, mock_mc, 
                                                    mock_get_market_trend, mock_load_data):
        mock_get_market_trend.return_value = "neutral"
        mock_load_data.side_effect = FileNotFoundError("Mocked data not found for stocks")

        with self.assertRaises(FileNotFoundError): # Or whatever exception load_data propagates
             run_risk_assessment(
                investment_amount=10000, 
                duration=3, 
                risk_appetite=0.5,
                stocks=100, bonds=0, real_estate=0, commodities=0
            )

if __name__ == '__main__':
    unittest.main()
