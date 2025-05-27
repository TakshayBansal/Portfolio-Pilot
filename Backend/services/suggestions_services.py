import pandas as pd
import numpy as np
import time # Added for timing
from Backend.utils.data_loader import load_data, get_top_50_stock_tickers
from models.portfolio_optimizer import optimize_stock_allocation, optimize_portfolio
from models.monte_carlo import monte_carlo_simulation
from models.gbm_model import geometric_brownian_motion

def get_optimized_portfolio(investment, duration, user_allocation, risk_tolerance):
    
    """
    Loads historical data and runs portfolio optimization based on user inputs.
    Also optimizes stock allocation within the 'Stocks' category.
    """
    try:
       
        stock_data = load_data("stocks")
        bond_data = load_data("bonds")
        real_estate_data = load_data("real_estate")
        commodity_data = load_data("commodities")

        data = pd.concat([
            stock_data['Close'],
            bond_data['Close'],
            real_estate_data['Close'],
            commodity_data['Close']
        ], axis=1)

        data.columns = ['Stocks', 'Bonds', 'Real_Estate', 'Commodities']

        optimized_weights = optimize_portfolio(data, user_allocation, risk_tolerance)
        allocation = {asset: round(weight, 2) for asset, weight in zip(data.columns, optimized_weights)}

    
        investment_breakdown = {asset: weight * investment for asset, weight in allocation.items()}
         
        # Get the list of top 50 stock tickers
        tickers = get_top_50_stock_tickers()
        
        print("Starting data fetch for top 50 stocks.") # Using print as logger not set up
        start_time = time.time()
        
        # Load data for each stock ticker
        stock_data = {}
        for ticker in tickers:
            try:
                stock_data[ticker] = load_data(ticker)
            except Exception as e:
                print(f"⚠️ Warning: Could not load data for {ticker}: {e}")
                # Optionally, decide if you want to skip this ticker or raise an error
                # For now, we'll skip it and the optimizer will work with fewer stocks
                continue # Skip to the next ticker if data loading fails
        
        duration_fetch = time.time() - start_time
        print(f"Finished data fetch for {len(stock_data)} out of {len(tickers)} stocks in {duration_fetch:.2f} seconds.")

        if not stock_data: # Check if stock_data is empty
             return {"error": "Could not load data for any stock tickers. Portfolio optimization aborted."}


        stock_investment = investment_breakdown.get("Stocks", 0)

        
       
        
        returns = data.pct_change().dropna()

        if returns.max().max() > 1:
            returns = returns / 100  
        risk_free_rate = 5  
        expected_return = np.dot(returns.mean(), optimized_weights) *252*  100  # Convert to %
        cov_matrix = returns.cov()
        volatility = np.sqrt(np.dot(optimized_weights.T, np.dot(cov_matrix, optimized_weights))) * np.sqrt(252) * 100

        sharpe_ratio = (expected_return - risk_free_rate / 100) / volatility if volatility > 0 else 0
        diversification_score = 1 / np.sum(np.square(optimized_weights)) if np.sum(np.square(optimized_weights)) != 0 else 0

        print("Starting stock allocation optimization.") # Using print
        opt_start_time = time.time()
        
        optimized_stock_allocation = optimize_stock_allocation(stock_data, risk_tolerance,duration)
        
        opt_duration = time.time() - opt_start_time
        print(f"Finished stock allocation optimization in {opt_duration:.2f} seconds.")
       
        if "error" in optimized_stock_allocation:
            return {"error": "Stock allocation optimization failed."}

        
        stock_allocation_investment = {
            stock: round((weight / 100) * stock_investment, 2)
            for stock, weight in optimized_stock_allocation.items()
        }
        suggestions = []

        if expected_return < 7:
            suggestions.append({
                "title": "Boost Expected Returns",
                "content": "Your portfolio's expected return is below market average (~7-10%). Adjust allocations for better growth potential."
            })

        if volatility > 25:
            suggestions.append({
                "title": "Reduce Portfolio Risk",
                "content": "Your portfolio has high volatility (>25%). Consider adding bonds or defensive stocks to stabilize performance."
            })

        if sharpe_ratio < 1:
            suggestions.append({
                "title": "Improve Risk-Adjusted Returns",
                "content": "Your Sharpe Ratio is below 1, indicating low return for risk taken. Consider adjusting asset allocation to improve efficiency."
            })

        if diversification_score < 0.05:
            suggestions.append({
                "title": "Increase Diversification",
                "content": "Your portfolio is heavily concentrated in a few assets. Consider reallocating to improve risk-adjusted returns."
            })

        return {
            "optimized_allocation": allocation,
            "investment_breakdown": investment_breakdown,
            "optimized_stock_allocation": optimized_stock_allocation,
            "stock_allocation_investment": stock_allocation_investment,
            "portfolio_metrics": {
                "Expected Return (%)": round(expected_return, 2),
                "Risk (Volatility %)": round(volatility, 2),
                "Sharpe Ratio": round(sharpe_ratio, 2),
                # "Diversification Score": round(diversification_score, 2)
            },
            "insights": suggestions
        }

    

    except Exception as e:
        print(f"Error during portfolio optimization: {e}")
        return {"error": "Failed to optimize portfolio. Please check the input data and try again."}