import numpy as np 
import pandas as pd
from models.monte_carlo import monte_carlo_simulation
from models.gbm_model import geometric_brownian_motion
from utils.data_loader import load_data




def run_simulation(investment_amount, duration, risk_appetite, market_condition, stocks, bonds, real_estate, commodities):
    """
    Runs investment simulation and returns key portfolio metrics including yearly values.
    """
    asset_classes = {
        "stocks": stocks,
        "bonds": bonds,
        "real_estate": real_estate,
        "commodities": commodities
    }

    total_final_monte_carlo = 0
    total_final_gbm = 0
    yearly_monte_carlo_values = np.zeros(duration + 1)  
    yearly_gbm_values = np.zeros(duration + 1)  

    avg_monte_carlo_return = 0
    avg_gbm_return = 0
    avg_volatility = 0
    avg_max_drawdown = 0

    num_assets = sum(1 for allocation in asset_classes.values() if allocation > 0)

    for asset, allocation in asset_classes.items():
        if allocation == 0:
            continue

        data = load_data(asset)
        returns = data['Close'].pct_change().dropna()
        mean_return = returns.mean()
        volatility = returns.std()

        # Market condition adjustments
        if market_condition == "bull":
            mean_return *= 1.2
        elif market_condition == "bear":
            mean_return *= 0.8

        volatility *= (1 + risk_appetite)
        asset_investment = investment_amount * (allocation / 100)
        # annualized_return = (1 + mean_return) ** 252 - 1

        # Run Monte Carlo and GBM simulations
        final_monte_carlo, yearly_monte_carlo = monte_carlo_simulation(asset_investment, mean_return, volatility, duration)
        final_gbm, yearly_gbm = geometric_brownian_motion(asset_investment, mean_return, volatility, duration)
    
        # Aggregate final values
        total_final_monte_carlo += np.mean(final_monte_carlo)
        total_final_gbm += np.mean(final_gbm)

        # Aggregate yearly values
        # Ensure yearly values are of the same length
        min_length = min(len(yearly_monte_carlo_values), len(yearly_gbm_values), len(yearly_monte_carlo), len(yearly_gbm))

# Trim arrays to the minimum length
        yearly_monte_carlo_values = yearly_monte_carlo_values[:min_length]
        yearly_gbm_values = yearly_gbm_values[:min_length]
        yearly_monte_carlo = yearly_monte_carlo[:min_length]
        yearly_gbm = yearly_gbm[:min_length]

        # Now add safely
      
        yearly_monte_carlo_values += yearly_monte_carlo
        yearly_gbm_values += yearly_gbm
        
        # Compute risk metrics
        # avg_monte_carlo_return += mean_return
        # avg_gbm_return += mean_return
        avg_volatility += volatility
        avg_max_drawdown += (returns.cummin() - returns).min()  # Max drawdown formula

    # Compute final values
    # final_total_value = (total_final_monte_carlo + total_final_gbm) / 2
    # print( final_total_value)
    monte_carlo_return = (total_final_monte_carlo / investment_amount) - 1
    gbm_return = (total_final_gbm / investment_amount) - 1
    print(monte_carlo_return)
    print(gbm_return)
    # final_avg_return = (monte_carlo_return+gbm_return)/2


    
    avg_volatility /= num_assets
    avg_max_drawdown /= num_assets
    avg_max_drawdown = avg_max_drawdown

    # Compute Sharpe Ratio (Risk-Adjusted Return)
    # risk_free_rate = 0.04  # Assuming 4% annual risk-free rate
    
    # sharpe_ratio = (cagr - risk_free_rate) / avg_volatility if avg_volatility > 0 else 0

    # Compute final yearly values for the graph
    # print(yearly_gbm_values)
    yearly_avg_values = (yearly_monte_carlo_values + yearly_gbm_values) / (2  )
    final_total_value = yearly_avg_values[-1]
    cagr = ((final_total_value / investment_amount) ** (1 / duration)) - 1
    sharpe_ratio = (cagr ) / avg_volatility if avg_volatility > 0 else 0
    # print(yearly_avg_values[-1])

    return {
        "Final Total Portfolio Value": round(final_total_value, 2),
        "Final Expected Return (%)": round(cagr * 100, 2),
        "Yearly Portfolio Values": [round(value, 2) for value in yearly_avg_values.tolist()],  
        "Volatility (%)": round(avg_volatility * 100, 2),
        "Sharpe Ratio": round(sharpe_ratio, 2),
        "Max Drawdown (%)": round(avg_max_drawdown , 2)
    }
