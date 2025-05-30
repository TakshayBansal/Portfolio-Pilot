import pandas as pd
import numpy as np
import scipy.optimize as sco  
from scipy.optimize import minimize
import math # Added for isnan, isinf

# Helper function to sanitize values for JSON compatibility
def sanitize_value(value):
    if isinstance(value, (float, np.floating)): # Handle both Python floats and numpy floats
        if math.isinf(value) or math.isnan(value):
            return None  # Replace inf/nan with None (will become null in JSON)
    elif isinstance(value, list) or isinstance(value, np.ndarray): # Handle lists and numpy arrays
        return [sanitize_value(item) for item in value]
    elif isinstance(value, dict): # If the value is a dict, sanitize each value
        return {k: sanitize_value(v) for k, v in value.items()}
    return value

def optimize_stock_allocation(stock_data, risk_tolerance, duration):
    """
    Optimizes stock allocation within the 'Stocks' category using Modern Portfolio Theory (MPT),
    factoring in risk tolerance and investment duration.
    """
    print(f"Starting optimize_stock_allocation for {len(stock_data)} stocks.") # Using print
    try:
       
        prices = pd.DataFrame({ticker: data['Close'] for ticker, data in stock_data.items()})
        returns = prices.pct_change().dropna()

       
        if prices.isnull().values.any():
            raise ValueError("Stock price data contains NaN values, please clean it.")

        if (returns.std() == 0).any():
            raise ValueError("Some stocks have zero volatility, check data.")

        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        num_stocks = len(stock_data)

        
        risk_aversion = (1 - risk_tolerance) * (1 / duration)  

        
        def objective_function(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(portfolio_return - risk_aversion * portfolio_volatility)  # Negative for minimization

      
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

        # Allow stocks to have zero allocation, especially with a larger number of stocks
        bounds = tuple((0.0, 1.0) for _ in range(num_stocks))

        
        best_result = None
        best_weights = None
        best_value = float("inf")

        # Reduced iterations from 1000 to 100 for performance with more assets.
        # This may slightly reduce the chance of finding the absolute global optimum.
        for _ in range(100):  
            initial_weights = np.random.dirichlet(np.ones(num_stocks), size=1)[0]  
            result = sco.minimize(objective_function, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)

            if result.success and result.fun < best_value:
                best_result = result
                best_weights = result.x
                best_value = result.fun

        if best_result is None:
            return {"error": "Stock optimization failed."}

      
        optimized_weights = best_weights / np.sum(best_weights)
        # Sanitize each weight individually
        sanitized_weights = [sanitize_value(w) for w in optimized_weights]
        
        result_allocation = {
            stock: round(weight * 100, 2) if weight is not None else None 
            for stock, weight in zip(stock_data.keys(), sanitized_weights)
        }
        print(f"Optimization attempt completed for {num_stocks} stocks.") # Using print
        return result_allocation

    except Exception as e:
        print(f"Error optimizing stock allocation for {len(stock_data)} stocks: {e}")
        print(f"Optimization attempt completed for {len(stock_data)} stocks with error.") # Using print
        # Error dictionary is inherently JSON compliant with string values
        return {"error": "Stock allocation optimization failed."}




def optimize_portfolio(price_data, user_allocation, risk_tolerance):
    """
    Performs Mean-Variance Portfolio Optimization (MPT) with user preferences.

    :param price_data: DataFrame with historical closing prices.
    :param user_allocation: User-defined initial allocation (list of weights).
    :param risk_tolerance: User's risk preference (0 = low, 1 = high).
    :return: Optimized asset allocation weights in percentage.
    """
    returns = price_data.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    num_assets = len(mean_returns)

    # Objective function: Adjust Sharpe Ratio for user risk preference
    def neg_sharpe(weights):
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio =  (portfolio_return ** risk_tolerance) / portfolio_volatility

        return -sharpe_ratio  

    
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

    
    bounds = tuple((0.05, 1) for _ in range(num_assets))

  
    initial_weights = np.array(user_allocation)

  
    result = sco.minimize(neg_sharpe, initial_weights, bounds=bounds, constraints=constraints)
    if not result.success:
        return {"error": "Portfolio optimization failed."}


    optimized_weights = result.x / np.sum(result.x)  
    
    # Sanitize each weight individually before scaling
    sanitized_weights_list = [sanitize_value(w) for w in optimized_weights]
    
    # Return a list of scaled weights (or None for sanitized items)
    return [w * 100 if w is not None else None for w in sanitized_weights_list]