import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import sys
import os
import math # Added for math.nan

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
        
        TRADING_DAYS_PER_YEAR = 252
        risk_appetite_input = 0.5 # Matches the input to run_risk_assessment

        # Calculate expected annualized inputs for stocks
        adj_stock_daily_mean_return = expected_stock_daily_mean_return # Already adjusted for market trend
        stock_daily_vol_raw = mock_stock_data['Close'].pct_change().dropna().std()
        adj_stock_daily_vol = stock_daily_vol_raw * (1 + risk_appetite_input / 100.0)
        
        expected_annual_stock_mean_return = adj_stock_daily_mean_return * TRADING_DAYS_PER_YEAR
        expected_annual_stock_volatility = adj_stock_daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)
        
        # Calculate expected annualized inputs for bonds
        adj_bond_daily_mean_return = expected_bond_daily_mean_return # Already adjusted for market trend
        bond_daily_vol_raw = mock_bond_data['Close'].pct_change().dropna().std()
        adj_bond_daily_vol = bond_daily_vol_raw * (1 + risk_appetite_input / 100.0)

        expected_annual_bond_mean_return = adj_bond_daily_mean_return * TRADING_DAYS_PER_YEAR
        expected_annual_bond_volatility = adj_bond_daily_vol * math.sqrt(TRADING_DAYS_PER_YEAR)

        # Check calls to simulation functions
        # We need to check asset_investment, annual_mean_return, annual_volatility, duration
        stock_asset_investment = 10000 * (50 / 100.0) # 50 is stocks allocation
        bond_asset_investment = 10000 * (50 / 100.0)  # 50 is bonds allocation
        duration_input = 3 # Matches input

        # Check that simulation functions were called with these annualized parameters
        # Using assert_any_call because the order of processing assets (stocks, bonds) isn't guaranteed fixed
        mock_mc.assert_any_call(stock_asset_investment, expected_annual_stock_mean_return, expected_annual_stock_volatility, duration_input)
        mock_gbm.assert_any_call(stock_asset_investment, expected_annual_stock_mean_return, expected_annual_stock_volatility, duration_input)
        mock_mc.assert_any_call(bond_asset_investment, expected_annual_bond_mean_return, expected_annual_bond_volatility, duration_input)
        mock_gbm.assert_any_call(bond_asset_investment, expected_annual_bond_mean_return, expected_annual_bond_volatility, duration_input)

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

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation')
    @patch('services.risk_assessment.geometric_brownian_motion')
    def test_run_risk_assessment_with_non_compliant_values(self, mock_gbm, mock_mc, 
                                                            mock_get_market_trend, mock_load_data):
        print("Testing Risk Assessment: Non-compliant values sanitization")
        mock_get_market_trend.return_value = "neutral"
        
        # Mock load_data to return some valid data so it doesn't fail early
        mock_asset_data = self.create_mock_asset_data([100, 101, 102, 103, 104])
        mock_load_data.return_value = mock_asset_data

        # Mock simulations to return non-compliant values
        mock_mc.return_value = (float('inf'), [1.0, math.nan, 3.0]) 
        mock_gbm.return_value = (float('-inf'), [float('inf'), 2.0, math.nan])

        result = run_risk_assessment(
            investment_amount=10000, 
            duration=3, 
            risk_appetite=0.5,
            stocks=100, # Single asset for simplicity in this test
            bonds=0, real_estate=0, commodities=0
        )
        
        self.assertNotIn("error", result)
        # final_total_value = (inf + -inf) / 2 = nan for many cases, or could be inf if one is much larger.
        # It depends on how inf arithmetic is handled before sanitization.
        # Assuming it results in something that sanitize_value turns to None.
        self.assertIsNone(result["Total Profit"], "Total Profit should be None due to inf values")
        
        # ROI is derived from total_monte_carlo_return and total_gbm_return which are inf/-inf
        # (inf/investment - 1) = inf. ( (inf + -inf)/1 ) for avg_..._return
        self.assertIsNone(result["ROI (%)"], "ROI (%) should be None")
        
        # Yearly values are averaged then sanitized.
        # MC: [1.0, nan, 3.0] -> after np.mean (if yearly_monte_carlo_values has only this one list) -> [1.0, nan, 3.0]
        # GBM: [inf, 2.0, nan] -> after np.mean -> [inf, 2.0, nan]
        # Then sanitize_value is applied to these lists.
        self.assertEqual(result["Yearly Monte Carlo Values"], [1.0, None, 3.0])
        self.assertEqual(result["Yearly GBM Values"], [None, 2.0, None])
        
        # Sharpe ratio might also be None if final_avg_return or avg_volatility is None
        # In this case, final_avg_return will be None.
        self.assertIsNone(result["Reward to Risk Ratio (Sharpe Ratio)"], "Sharpe Ratio should be None")
        
        # Risk score could also be None if avg_volatility or avg_max_drawdown becomes None
        # avg_max_drawdown comes from data['Close'] which is fine.
        # avg_volatility comes from data['Close'].pct_change().std() which is fine.
        # So risk_score itself might be a number, unless one of its components (like sharpe) was used in a way that made it NaN.
        # The current risk_score formula: 5 + (avg_volatility * 10) - (avg_max_drawdown * 5)
        # If avg_volatility is a valid number, and avg_max_drawdown is valid, risk_score should be a number.
        # Let's assume it is for this test, as we are primarily testing the simulation outputs.
        self.assertIsNotNone(result["Risk Score"]) # Assuming volatility and drawdown are not NaN/inf from the mock_asset_data

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation') # Still need to mock these
    @patch('services.risk_assessment.geometric_brownian_motion') # Still need to mock these
    def test_run_risk_assessment_zero_volatility(self, mock_gbm, mock_mc, 
                                                 mock_get_market_trend, mock_load_data):
        print("Testing Risk Assessment: Zero volatility for Sharpe Ratio")
        mock_get_market_trend.return_value = "neutral"
        
        # Mock load_data to return data with zero volatility (constant prices)
        mock_zero_vol_data = self.create_mock_asset_data([100, 100, 100, 100, 100])
        mock_load_data.return_value = mock_zero_vol_data # All assets will have zero volatility

        # Mock simulations to return some valid numbers, so they don't cause None
        mock_mc.return_value = (10100, [10000, 10050, 10100]) 
        mock_gbm.return_value = (10100, [10000, 10050, 10100])

        result = run_risk_assessment(
            investment_amount=10000, 
            duration=3, 
            risk_appetite=0.1, # Low risk appetite
            stocks=100, 
            bonds=0, real_estate=0, commodities=0
        )
        self.assertNotIn("error", result)
        # avg_volatility will be 0. sharpe_ratio = final_avg_return / avg_volatility
        # This will lead to division by zero -> inf (or -inf or nan depending on final_avg_return)
        # So, sanitized Sharpe Ratio should be None.
        self.assertIsNone(result["Reward to Risk Ratio (Sharpe Ratio)"], 
                          "Sharpe Ratio should be None due to zero volatility")
        self.assertIsNotNone(result["Total Profit"]) # Should be a number based on mock mc/gbm
        self.assertIsNotNone(result["ROI (%)"])     # Should be a number

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation')
    @patch('services.risk_assessment.geometric_brownian_motion')
    def test_run_risk_assessment_profit_capping(self, mock_gbm, mock_mc, 
                                                 mock_get_market_trend, mock_load_data):
        print("Testing Risk Assessment: Profit Capping")
        mock_get_market_trend.return_value = "neutral"
        mock_asset_data = self.create_mock_asset_data([100, 101, 102])
        mock_load_data.return_value = mock_asset_data
        
        MAX_REASONABLE_PROFIT = 1e12 # From the module

        # Test positive profit capping
        mock_mc.return_value = (MAX_REASONABLE_PROFIT * 2, [10000, 1e12, 2e12]) 
        mock_gbm.return_value = (MAX_REASONABLE_PROFIT * 2, [10000, 1e12, 2e12])
        
        result_positive_cap = run_risk_assessment(
            investment_amount=10000, duration=3, risk_appetite=0.1,
            stocks=100, bonds=0, real_estate=0, commodities=0
        )
        self.assertNotIn("error", result_positive_cap)
        self.assertEqual(result_positive_cap["Total Profit"], MAX_REASONABLE_PROFIT)

        # Test negative profit capping
        mock_mc.return_value = (-MAX_REASONABLE_PROFIT * 2, [10000, -1e12, -2e12])
        mock_gbm.return_value = (-MAX_REASONABLE_PROFIT * 2, [10000, -1e12, -2e12])

        result_negative_cap = run_risk_assessment(
            investment_amount=10000, duration=3, risk_appetite=0.1,
            stocks=100, bonds=0, real_estate=0, commodities=0
        )
        self.assertNotIn("error", result_negative_cap)
        self.assertEqual(result_negative_cap["Total Profit"], -MAX_REASONABLE_PROFIT)

    @patch('services.risk_assessment.load_data')
    @patch('services.risk_assessment.get_market_trend')
    @patch('services.risk_assessment.monte_carlo_simulation')
    @patch('services.risk_assessment.geometric_brownian_motion')
    def test_run_risk_assessment_roi_capping(self, mock_gbm, mock_mc, 
                                             mock_get_market_trend, mock_load_data):
        print("Testing Risk Assessment: ROI Capping")
        mock_get_market_trend.return_value = "neutral"
        mock_asset_data = self.create_mock_asset_data([100, 101, 102])
        mock_load_data.return_value = mock_asset_data

        MAX_REASONABLE_ROI_FACTOR = 10000 # From the module
        investment_amount = 1000 # For easier calculation

        # Test positive ROI capping
        # final_avg_return = ( (sim_val_mc/inv - 1) + (sim_val_gbm/inv - 1) ) / 2
        # To make final_avg_return > MAX_REASONABLE_ROI_FACTOR
        # Let each (sim_val/inv - 1) be MAX_REASONABLE_ROI_FACTOR + 100
        # So, sim_val = investment_amount * (MAX_REASONABLE_ROI_FACTOR + 101)
        sim_val_high_roi = investment_amount * (MAX_REASONABLE_ROI_FACTOR + 101)
        mock_mc.return_value = (sim_val_high_roi, [investment_amount, sim_val_high_roi/2, sim_val_high_roi])
        mock_gbm.return_value = (sim_val_high_roi, [investment_amount, sim_val_high_roi/2, sim_val_high_roi])
        
        result_positive_roi_cap = run_risk_assessment(
            investment_amount=investment_amount, duration=3, risk_appetite=0.1,
            stocks=100, bonds=0, real_estate=0, commodities=0
        )
        self.assertNotIn("error", result_positive_roi_cap)
        # ROI (%) = final_avg_return * 100. We capped final_avg_return at MAX_REASONABLE_ROI_FACTOR
        self.assertEqual(result_positive_roi_cap["ROI (%)"], MAX_REASONABLE_ROI_FACTOR * 100)

        # Test negative ROI capping (-100% or -1.0 factor)
        # To make final_avg_return < -1.0
        # Let each (sim_val/inv - 1) be -2.0
        # So, sim_val = investment_amount * (-2.0 + 1) = -investment_amount
        sim_val_neg_roi = -investment_amount 
        mock_mc.return_value = (sim_val_neg_roi, [investment_amount, 0, sim_val_neg_roi])
        mock_gbm.return_value = (sim_val_neg_roi, [investment_amount, 0, sim_val_neg_roi])

        result_negative_roi_cap = run_risk_assessment(
            investment_amount=investment_amount, duration=3, risk_appetite=0.1,
            stocks=100, bonds=0, real_estate=0, commodities=0
        )
        self.assertNotIn("error", result_negative_roi_cap)
        # final_avg_return capped at -1.0. ROI (%) = -1.0 * 100
        self.assertEqual(result_negative_roi_cap["ROI (%)"], -100.0)


if __name__ == '__main__':
    unittest.main()
