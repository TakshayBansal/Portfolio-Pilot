import numpy as np 
import pandas as pd
import math # Added for isnan, isinf
from models.monte_carlo import monte_carlo_simulation
from models.gbm_model import geometric_brownian_motion
from utils.data_loader import load_data
<<<<<<< Updated upstream
=======
from utils.market_trend import get_market_trend

# Define sanity cap thresholds at module level
MAX_REASONABLE_PROFIT = 1e12  # 1 Trillion
MAX_REASONABLE_ROI_FACTOR = 10000  # Corresponds to 1,000,000% ROI (ROI as a factor, e.g., 10000x)

# Define thresholds and defaults for insufficient data handling
MIN_RETURNS_DATA_POINTS = 60  # Approx 3 months of trading days
DEFAULT_CONSERVATIVE_DAILY_MEAN = 0.0001  # 0.01% daily return
DEFAULT_CONSERVATIVE_DAILY_VOL = 0.01    # 1% daily volatility
DEFAULT_CONSERVATIVE_MAX_DRAWDOWN = -0.10 # 10% max drawdown

# Helper function to sanitize values for JSON compatibility
def sanitize_value(value):
    if isinstance(value, (float, np.floating)): # Handle both Python floats and numpy floats
        if math.isinf(value) or math.isnan(value):
            return None  # Replace inf/nan with None (will become null in JSON)
    elif isinstance(value, list): # If the value is a list, sanitize each element
        return [sanitize_value(item) for item in value]
    # The prompt had a dict example, but it's not strictly needed for this specific return structure.
    # If future return values become complex dicts, that part can be added.
    # elif isinstance(value, dict): 
    #     return {k: sanitize_value(v) for k, v in value.items()}
    return value
>>>>>>> Stashed changes

def run_risk_assessment(investment_amount, duration, risk_appetite, market_condition, stocks, bonds, real_estate, commodities):
    asset_classes = {
        "stocks": stocks,
        "bonds": bonds,
        "real_estate": real_estate,
        "commodities": commodities
    }
    
    total_monte_carlo_value = 0
    total_gbm_value = 0
    total_monte_carlo_return = 0
    total_gbm_return = 0
    total_volatility = 0
    
    avg_max_drawdown=0
    
    yearly_monte_carlo_values = []
    yearly_gbm_values = []
    
    num_assets = sum(1 for allocation in asset_classes.values() if allocation > 0)
    if num_assets == 0:
        return {"error": "At least one asset must have an allocation greater than 0."}

    for asset, allocation in asset_classes.items():
        if allocation == 0:
            continue

        data = load_data(asset)
        returns = data['Close'].pct_change().dropna()
        mean_return = data['Close'].pct_change().dropna().mean()
        volatility = data['Close'].pct_change().dropna().std()
        cumulative_max = data['Close'].cummax()  # Track all-time highest prices
        drawdown = (data['Close'] / cumulative_max) - 1  # Drop from peak at each point
        max_drawdown = drawdown.min()  # Worst drop from any peak

<<<<<<< Updated upstream

        # Adjust return based on market condition
        if market_condition == "bull":
            mean_return *= 1.2  # 20% boost in bull market
        elif market_condition == "bear":
            mean_return *= 0.8  # 20% drop in bear market
=======
        print(f"--- DIAGNOSTIC --- Asset: {asset}, Allocation: {allocation}%")
        print(f"--- DIAGNOSTIC --- Num Returns Points: {len(returns)}")
        print(f"--- DIAGNOSTIC --- Calculated Daily Mean Return: {mean_return}")
        print(f"--- DIAGNOSTIC --- Calculated Daily Volatility: {volatility}")
        print(f"--- DIAGNOSTIC --- Calculated Max Drawdown (raw): {max_drawdown}")

        # Fallback to conservative defaults if insufficient data points
        if len(returns) < MIN_RETURNS_DATA_POINTS:
            print(f"--- WARNING --- Asset: {asset} has only {len(returns)} return points (less than {MIN_RETURNS_DATA_POINTS}). Using conservative default statistics.")
            mean_return = DEFAULT_CONSERVATIVE_DAILY_MEAN
            volatility = DEFAULT_CONSERVATIVE_DAILY_VOL
            max_drawdown = DEFAULT_CONSERVATIVE_MAX_DRAWDOWN
            print(f"--- DIAGNOSTIC --- Using Defaults - Mean: {mean_return}, Vol: {volatility}, Max Drawdown: {max_drawdown}")


        # Adjust return based on automatically determined market trend
        adjustment_factor = 1.0 # Default for neutral or if trend is unclear
        if market_trend_actual == "bull":
            adjustment_factor = 1.1 # 10% boost for bull
        elif market_trend_actual == "bear":
            adjustment_factor = 0.9 # 10% reduction for bear
        
        mean_return *= adjustment_factor
>>>>>>> Stashed changes
        
        # Adjust risk based on risk appetite
        volatility *= (1 + risk_appetite / 100.0)

        # Annualize mean_return and volatility
        TRADING_DAYS_PER_YEAR = 1
        annual_mean_return = mean_return * TRADING_DAYS_PER_YEAR
        annual_volatility = volatility * math.sqrt(TRADING_DAYS_PER_YEAR)

        # Compute initial investment for this asset
        asset_investment = investment_amount * (allocation / 100)

        # Run simulations with annualized inputs
        final_monte_carlo_value, monte_carlo_yearly_values = monte_carlo_simulation(asset_investment, annual_mean_return, annual_volatility, duration)
        final_gbm_value, gbm_yearly_values = geometric_brownian_motion(asset_investment, annual_mean_return, annual_volatility, duration)

        # Store yearly values
        yearly_monte_carlo_values.append(monte_carlo_yearly_values)
        yearly_gbm_values.append(gbm_yearly_values)

        # Aggregate final values
        total_monte_carlo_value += final_monte_carlo_value
        total_gbm_value += final_gbm_value
        total_monte_carlo_return += (final_monte_carlo_value / asset_investment) - 1
        total_gbm_return += (final_gbm_value / asset_investment) - 1
        total_volatility += volatility
        # total_max_drawdown += max_drawdown avg_max_drawdown += (returns.cummin() - returns).min() 
        # cumulative_max = data['Close'].cummax()
        # drawdown = (data['Close'] / cumulative_max) - 1  # Convert to percentage loss
        # max_drawdown = drawdown.min()  # Largest drop from peak

        avg_max_drawdown += max_drawdown  # Sum up, we'll average later


    # Compute final values and returns
    avg_monte_carlo_return = total_monte_carlo_return / num_assets
    avg_gbm_return = total_gbm_return / num_assets
    final_total_value = (total_monte_carlo_value + total_gbm_value) / 2
    final_avg_return = (avg_monte_carlo_return + avg_gbm_return) / 2
    
    # Apply sanity caps to final_total_value
    if final_total_value > MAX_REASONABLE_PROFIT:
        print(f"⚠️ Capping final_total_value from {final_total_value} to {MAX_REASONABLE_PROFIT}")
        final_total_value = MAX_REASONABLE_PROFIT
    elif final_total_value < -MAX_REASONABLE_PROFIT: # Also cap extreme losses
        print(f"⚠️ Capping final_total_value from {final_total_value} to {-MAX_REASONABLE_PROFIT}")
        final_total_value = -MAX_REASONABLE_PROFIT

    # Apply sanity caps to final_avg_return (which is a factor here, not percentage)
    if final_avg_return > MAX_REASONABLE_ROI_FACTOR:
        print(f"⚠️ Capping final_avg_return from {final_avg_return} to {MAX_REASONABLE_ROI_FACTOR}")
        final_avg_return = MAX_REASONABLE_ROI_FACTOR
    elif final_avg_return < -1.0: # ROI factor should not be less than -1 (-100% loss)
        print(f"⚠️ Capping final_avg_return from {final_avg_return} to -1.0")
        final_avg_return = -1.0

    avg_volatility = total_volatility / num_assets
    avg_max_drawdown /= num_assets
    sharpe_ratio = final_avg_return / avg_volatility if avg_volatility > 0 else 0

    # Compute Risk Score (0-10)
<<<<<<< Updated upstream
    risk_score = 5 + (avg_volatility * 10) - (avg_max_drawdown * 5)
    if market_condition == "bull":
        risk_score -= 0.5
    elif market_condition == "bear":
        risk_score += 0.5
    risk_score = max(0, min(10, risk_score))  # Ensure within 0-10
=======
    # Example: assume volatility and drawdown are normalized between 0 and 1
    normalized_volatility = avg_volatility / 0.8  # assuming max expected = 0.8
    normalized_drawdown = avg_max_drawdown / 0.5  # assuming max expected = 0.5

    # Compute risk score
    risk_score = 2.5 + (normalized_volatility * 4) - (normalized_drawdown * 2)

    # Adjust for market trend
    if market_trend_actual == "bull":
        risk_score -= 1
    elif market_trend_actual == "bear":
        risk_score += 0.6

    # Clip to 0-10 range
    risk_score = max(0, min(10, risk_score))


    # Sanitize all numerical values before rounding and returning
    final_total_value_sanitized = sanitize_value(final_total_value)
    final_avg_return_sanitized = sanitize_value(final_avg_return)
    avg_max_drawdown_sanitized = sanitize_value(avg_max_drawdown)
    avg_volatility_sanitized = sanitize_value(avg_volatility)
    sharpe_ratio_sanitized = sanitize_value(sharpe_ratio)
    risk_score_sanitized = sanitize_value(risk_score)

    # Sanitize list values
    yearly_mc_values_processed = np.mean(yearly_monte_carlo_values, axis=0).tolist() if yearly_monte_carlo_values else []
    yearly_gbm_values_processed = np.mean(yearly_gbm_values, axis=0).tolist() if yearly_gbm_values else []
    
    yearly_mc_values_sanitized = sanitize_value(yearly_mc_values_processed)
    yearly_gbm_values_sanitized = sanitize_value(yearly_gbm_values_processed)

    print("Total Profit",round(final_total_value_sanitized, 2) if final_total_value_sanitized is not None else None)
    print("ROI (%)",round(final_avg_return_sanitized * 100, 2) if final_avg_return_sanitized is not None else None)
    print("Max Drawdown (%)", round(avg_max_drawdown_sanitized * 100, 2) if avg_max_drawdown_sanitized is not None else None)
    print("Volatility Score", round(avg_volatility_sanitized * 100, 2) if avg_volatility_sanitized is not None else None)
>>>>>>> Stashed changes

    return {
        "Total Profit": round(final_total_value_sanitized, 2) if final_total_value_sanitized is not None else None,
        "ROI (%)": round(final_avg_return_sanitized * 100, 2) if final_avg_return_sanitized is not None else None,
        "Max Drawdown (%)": round(avg_max_drawdown_sanitized * 100, 2) if avg_max_drawdown_sanitized is not None else None,
        "Volatility Score": round(avg_volatility_sanitized * 100, 2) if avg_volatility_sanitized is not None else None,
        "Reward to Risk Ratio (Sharpe Ratio)": round(sharpe_ratio_sanitized, 2) if sharpe_ratio_sanitized is not None else None,
        "Risk Score": round(risk_score_sanitized, 1) if risk_score_sanitized is not None else None,
        "Yearly Monte Carlo Values": yearly_mc_values_sanitized,
        "Yearly GBM Values": yearly_gbm_values_sanitized
    }
