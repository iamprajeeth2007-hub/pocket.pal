from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

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


def _linear_regression(x_vals: List[float], y_vals: List[float]) -> float:
    """
    Pure-Python ordinary least squares linear regression.
    Returns the prediction for the next x value (len(x_vals)).
    """
    n = len(x_vals)
    if n == 0:
        return 0.0

    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    denominator = sum((x - mean_x) ** 2 for x in x_vals)

    if denominator == 0:
        return mean_y  # All same x — just return average

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    next_x = float(n)  # next index after 0..n-1
    return slope * next_x + intercept


def predict_future_spending(expenses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Predicts the next month's spending based on historical expense data.
    Uses pure-Python linear regression (replaces scikit-learn + pandas + numpy).
    """
    if not expenses or len(expenses) < 3:
        # Fallback if there is not enough data
        total_amt = sum(float(e["amount"]) for e in expenses) if expenses else 0.0
        unique_months = len(set(e.get("date", "")[:7] for e in expenses if e.get("date"))) or 1
        avg_est = total_amt / unique_months
        return {
            "predicted_total": round(avg_est, 2),
            "method": "historical_average",
            "message": "Need data spanning at least 3 months for ML trend analysis. Showing average monthly spending.",
            "category_predictions": {}
        }

    # Group expenses by YYYY-MM month
    monthly_totals: Dict[str, float] = defaultdict(float)
    category_totals: Dict[str, float] = defaultdict(float)
    grand_total = 0.0

    for e in expenses:
        date_str = e.get("date", "")
        month_key = date_str[:7] if len(date_str) >= 7 else "unknown"
        amount = float(e["amount"])
        monthly_totals[month_key] += amount
        category_totals[e.get("category", "Others")] += amount
        grand_total += amount

    # Sort months chronologically
    sorted_months = sorted(monthly_totals.keys())
    y_vals = [monthly_totals[m] for m in sorted_months]
    x_vals = list(range(len(y_vals)))

    # Predict next month using OLS linear regression
    prediction = max(0.0, _linear_regression(x_vals, y_vals))

    # Distribute prediction across categories by historical proportion
    category_predictions = {}
    if grand_total > 0:
        category_predictions = {
            cat: round((amt / grand_total) * prediction, 2)
            for cat, amt in category_totals.items()
        }

    return {
        "predicted_total": round(prediction, 2),
        "method": "linear_regression",
        "message": f"ML model fitted over {len(sorted_months)} months of data.",
        "category_predictions": category_predictions
    }
