from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.suggestions_services import get_optimized_portfolio

router = APIRouter()

# Define request model
class PortfolioRequest(BaseModel):
    investment: float = Field(..., gt=0, description="Total investment amount")
    duration: int = Field(..., ge=1, le=30, description="Investment duration in years")
    risk_tolerance: float = Field(..., ge=0.01, le=1.0, description="User risk preference (0=Low, 1=High)")
    stocks: float = Field(..., ge=0, le=100, description="Initial allocation to Stocks")
    bonds: float = Field(..., ge=0, le=100, description="Initial allocation to Bonds")
    real_estate: float = Field(..., ge=0, le=100, description="Initial allocation to Real Estate")
    commodities: float = Field(..., ge=0, le=100, description="Initial allocation to Commodities")

@router.post("/portfolio_suggestions")
async def get_suggestions(request: PortfolioRequest):
    user_allocation = [
        request.stocks / 100,  # Convert to fractions
        request.bonds / 100,
        request.real_estate / 100,
        request.commodities / 100
    ]

    # Ensure allocations sum to 100%
    total_allocation = sum(user_allocation)
    print("📩 Raw Request Data:", request.dict())  # Debugging
    print("✅ Converted Allocation:", user_allocation)  # Debugging
    if not (0.99 <= total_allocation <= 1.01):
        raise HTTPException(status_code=400, detail="Allocations must sum to 100%.")

    # Get optimized allocation
    optimized_results = get_optimized_portfolio(
        request.investment, request.duration, user_allocation, request.risk_tolerance
    )
    print(optimized_results)

    # Check for errors from optimizer
    if "error" in optimized_results:
        raise HTTPException(status_code=500, detail=optimized_results["error"])

    return optimized_results  # Return full results