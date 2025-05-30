import unittest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import sys
import os
import json

# Ensure the Backend directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the router from your application
# Assuming your main app or a specific router module needs to be imported
# For this example, let's assume the risk_assessment router is in routes.risk_assessment
from routes.risk_assessment import router as risk_assessment_router
# If you have routers for other functionalities like suggestions, import them too.
# from routes.suggestions import router as suggestions_router # Example

# Create a FastAPI instance for testing
app = FastAPI()
app.include_router(risk_assessment_router, prefix="/risk", tags=["risk"]) # Match your actual prefix if any
# app.include_router(suggestions_router, prefix="/suggestions", tags=["suggestions"]) # Example

class TestRiskAssessmentAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch('services.risk_assessment.run_risk_assessment') # Target the service function
    def test_risk_assessment_api_success(self, mock_run_risk_assessment):
        print("Testing API: /risk-assessment success")
        
        # Mock the service layer function's return value
        mock_service_response = {
            "Total Profit": 12000.0,
            "ROI (%)": 20.0,
            "Max Drawdown (%)": 15.0,
            "Volatility Score": 10.0,
            "Reward to Risk Ratio (Sharpe Ratio)": 1.5,
            "Risk Score": 6.5,
            "Yearly Monte Carlo Values": [10000, 11000, 12000],
            "Yearly GBM Values": [10000, 11500, 12500]
        }
        mock_run_risk_assessment.return_value = mock_service_response

        # Define the payload for the API request (without market_condition)
        payload = {
            "investment_amount": 10000.0,
            "duration": 3, # years
            "risk_appetite": 0.6, # Example value (0.0 to 1.0 typically)
            "stocks": 60.0, # Percentage
            "bonds": 30.0,
            "real_estate": 5.0,
            "commodities": 5.0
        }

        # Make the POST request
        # Ensure the path matches how the router is included in the app
        # If router prefix is "/risk" and endpoint is "/risk-assessment", path is "/risk/risk-assessment"
        response = self.client.post("/risk/risk-assessment", json=payload) 

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), mock_service_response)
        
        # Verify that the service function was called with the correct arguments
        # (excluding market_condition)
        mock_run_risk_assessment.assert_called_once_with(
            investment_amount=payload["investment_amount"],
            duration=payload["duration"],
            risk_appetite=payload["risk_appetite"],
            stocks=payload["stocks"],
            bonds=payload["bonds"],
            real_estate=payload["real_estate"],
            commodities=payload["commodities"]
        )

    def test_risk_assessment_api_invalid_payload(self):
        print("Testing API: /risk-assessment invalid payload (missing field)")
        # Payload missing 'investment_amount'
        payload = {
            # "investment_amount": 10000.0, # Missing
            "duration": 3,
            "risk_appetite": 0.6,
            "stocks": 60.0,
            "bonds": 30.0,
            "real_estate": 5.0,
            "commodities": 5.0
        }
        response = self.client.post("/risk/risk-assessment", json=payload)
        
        # FastAPI typically returns 422 for Pydantic validation errors
        self.assertEqual(response.status_code, 422) 
        # Check for some detail in the error response if needed
        response_json = response.json()
        self.assertIn("detail", response_json)
        found_investment_amount_error = False
        for error in response_json["detail"]:
            if "investment_amount" in error.get("loc", []) and error.get("type") == "missing":
                 found_investment_amount_error = True
                 break
        self.assertTrue(found_investment_amount_error, "Error detail for missing 'investment_amount' not found.")


    # You can add similar tests for other API endpoints (e.g., suggestions)
    # by patching their respective service functions.

if __name__ == '__main__':
    # This allows running the tests directly with `python Backend/tests/test_api.py`
    # However, typically you'd use `python -m unittest discover Backend/tests` or pytest.
    unittest.main()
