import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from typing import List, Dict, Any

# Keyword rules for Smart Categorization
CATEGORIES = {
    "Food": ["dominos", "pizza", "burger", "restaurant", "food", "swiggy", "zomato", "kfc", "mcdonald", "diner", "cafe", "starbucks", "subway", "eats", "grocery", "groceries"],
    "Travel": ["uber", "ola", "taxi", "bus", "train", "metro", "irctc", "auto", "flight", "travel", "booking", "cab", "rapido"],
    "Shopping": ["amazon", "flipkart", "myntra", "clothing", "shop", "shoes", "clothes", "mall", "retail", "zara", "h&m"],
    "Recharge": ["jio", "airtel", "vodafone", "vi", "recharge", "bill", "electricity", "water", "internet", "wifi", "broadband", "netflix", "spotify", "prime"],
    "Petrol": ["petrol", "diesel", "fuel", "shell", "hpcl", "bpcl", "gas", "cng", "refuel"],
    "Others": []
}

def categorize_expense(description: str) -> str:
    """
    Categorizes an expense based on keywords. Matches are case-insensitive.
    If no match is found, defaults to 'Others'.
    """
    if not description:
        return "Others"
    
    desc_lower = description.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in desc_lower:
                return category
                
    return "Others"

def predict_future_spending(expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Predicts the next month's spending based on historical expense data.
    Uses pandas for data manipulation and scikit-learn LinearRegression for trend analysis.
    """
    if not expenses or len(expenses) < 3:
        # Fallback if there is not enough data
        total_amt = sum(float(e["amount"]) for e in expenses) if expenses else 0.0
        avg_est = total_amt / max(len(set(e.get("date", "")[:7] for e in expenses if e.get("date"))), 1)
        return {
            "predicted_total": round(avg_est, 2),
            "method": "historical_average",
            "message": "Need data spanning at least 3 months for ML trend analysis. Showing average monthly spending.",
            "category_predictions": {}
        }

    # Load into DataFrame
    df = pd.DataFrame(expenses)
    df["amount"] = df["amount"].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M")

    # Group by month and calculate monthly sums
    monthly_data = df.groupby("year_month")["amount"].sum().reset_index()
    monthly_data = monthly_data.sort_values("year_month")

    # Map year_month to consecutive integer indices for modeling
    monthly_data["month_index"] = np.arange(len(monthly_data))

    X = monthly_data[["month_index"]]
    y = monthly_data["amount"]

    # Fit linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict the next month index
    next_month_index = len(monthly_data)
    prediction = model.predict([[next_month_index]])[0]
    
    # Bound the prediction so it doesn't go negative
    prediction = max(0.0, float(prediction))

    # Calculate average category distribution percentage from history
    cat_distribution = df.groupby("category")["amount"].sum()
    total_spent = cat_distribution.sum()
    cat_percentages = (cat_distribution / total_spent).to_dict() if total_spent > 0 else {}

    # Distribute the prediction to categories
    category_predictions = {
        cat: round(pct * prediction, 2)
        for cat, pct in cat_percentages.items()
    }

    return {
        "predicted_total": round(prediction, 2),
        "method": "linear_regression",
        "message": f"ML model fitted over {len(monthly_data)} months of data.",
        "category_predictions": category_predictions
    }
