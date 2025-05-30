import pandas as pd
import numpy as np
<<<<<<< Updated upstream
from utils.data_loader import load_data
from models.portfolio_optimizer import optimize_stock_allocation, optimize_portfolio
from models.monte_carlo import monte_carlo_simulation
from models.gbm_model import geometric_brownian_motion
from utils.data_loader import load_data
=======
import time     # Timing
import math     # isnan, isinf

from utils.data_loader import load_data, get_top_50_stock_tickers
from models.portfolio_optimizer import optimize_stock_allocation, optimize_portfolio

# Helper to replace inf/nan with None for JSON
def sanitize_value(value):
    if isinstance(value, (float, np.floating)):
        if math.isinf(value) or math.isnan(value):
            return None
    elif isinstance(value, list):
        return [sanitize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    return value

>>>>>>> Stashed changes
def get_optimized_portfolio(investment, duration, user_allocation, risk_tolerance):
    """
    Returns a dict containing:
      - optimized_allocation: high-level weights for Stocks, Bonds, Real_Estate, Commodities
      - investment_breakdown: actual rupee allocation per asset
      - optimized_stock_allocation: breakdown within the Stocks bucket
      - stock_allocation_investment: rupee allocation per individual stock
      - portfolio_metrics: Expected Return %, Volatility %, Sharpe Ratio
      - insights: list of recommendation dicts {title, content}
    """
    try:
        # 1) Load market data
        stock_data = load_data("stocks")
        bond_data = load_data("bonds")
        real_estate_data = load_data("real_estate")
        commodity_data = load_data("commodities")

        data = pd.concat([
            stock_data["Close"],
            bond_data["Close"],
            real_estate_data["Close"],
            commodity_data["Close"],
        ], axis=1)
        data.columns = ["Stocks", "Bonds", "Real_Estate", "Commodities"]

        # 2) High-level allocation
        optimized_weights = optimize_portfolio(data, user_allocation, risk_tolerance)
        weights = np.array(optimized_weights)              # ← convert list→array
        allocation = {
            asset: round(w, 4)
            for asset, w in zip(data.columns, weights)
        }
        investment_breakdown = {
            asset: round(w * investment, 2)
            for asset, w in allocation.items()
        }

<<<<<<< Updated upstream
    
        investment_breakdown = {asset: weight * investment for asset, weight in allocation.items()}
         
      
        stock_list = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        stock_data = {ticker: load_data(ticker) for ticker in stock_list}
     
        stock_investment = investment_breakdown.get("Stocks", 0)

        
       
        
=======
        # 3) Fetch top-50 stock histories
        tickers = get_top_50_stock_tickers()
        stock_data_dict = {}
        start = time.time()
        for t in tickers:
            try:
                stock_data_dict[t] = load_data(t)
            except Exception as e:
                print(f"⚠️ Skipped {t}: {e}")
        print(f"Loaded {len(stock_data_dict)}/{len(tickers)} in {time.time()-start:.1f}s")

        if not stock_data_dict:
            return {"error": "No individual stock data available."}

        # 4) Portfolio metrics
>>>>>>> Stashed changes
        returns = data.pct_change().dropna()
        # If percentages >1, assume they were in basis points
        if returns.max().max() > 1:
            returns /= 100

        annual_factor = 252
        rf_rate = 0.05  # 5%

<<<<<<< Updated upstream
        
        optimized_stock_allocation = optimize_stock_allocation(stock_data, risk_tolerance,duration)

       
        if "error" in optimized_stock_allocation:
            return {"error": "Stock allocation optimization failed."}
=======
        mean_returns = returns.mean().values
        cov = returns.cov().values
>>>>>>> Stashed changes

        expected_return = float(np.dot(mean_returns, weights) * annual_factor * 100)
        volatility = float(np.sqrt(weights @ cov @ weights.T) * np.sqrt(annual_factor) * 100)
        sharpe = ((expected_return - rf_rate * 100) / volatility) if volatility > 0 else 0.0

        # 5) Stock-level optimization
        opt_start = time.time()
        stock_alloc = optimize_stock_allocation(stock_data_dict, risk_tolerance, duration)
        print(f"Stock optimize took {time.time()-opt_start:.1f}s")

        if "error" in stock_alloc:
            return {"error": "Error in stock-level optimization."}

        stock_bucket_amt = investment_breakdown["Stocks"]
        stock_alloc_invest = {
            t: round((w / 100) * stock_bucket_amt, 2)
            for t, w in stock_alloc.items()
        }

        # 6) Build insights
        insights = []
        if expected_return < 7:
            insights.append({
                "title": "Boost Expected Returns",
                "content": "Your expected return (<7%) is below market average. Consider heavier equities or higher-growth sectors."
            })
        if volatility > 25:
            insights.append({
                "title": "Reduce Portfolio Risk",
                "content": "Volatility is high (>25%). Increase bond or defensive allocations to smooth returns."
            })
        if sharpe < 1:
            insights.append({
                "title": "Improve Risk-Adjusted Returns",
                "content": "Sharpe Ratio <1 indicates low reward per unit risk. Consider rebalancing towards assets with better risk/reward."
            })

        # 7) Sanitize and round
        result = {
            "optimized_allocation": sanitize_value(allocation),
            "investment_breakdown": sanitize_value(investment_breakdown),
            "optimized_stock_allocation": sanitize_value(stock_alloc),
            "stock_allocation_investment": sanitize_value(stock_alloc_invest),
            "portfolio_metrics": {
                "Expected Return (%)": round(sanitize_value(expected_return), 2),
                "Volatility (%)": round(sanitize_value(volatility), 2),
                "Sharpe Ratio": round(sanitize_value(sharpe), 2),
            },
            "insights": insights
        }

        return result

    except Exception as e:
        print(f"Error during portfolio optimization: {e}")
        return {"error": "Portfolio optimization failed."}
