from datetime import datetime
from typing import List, Dict, Any

def calculate_financial_health_score(
    expenses: List[Dict[str, Any]], 
    limits: List[Dict[str, Any]], 
    monthly_income: float
) -> Dict[str, Any]:
    """
    Calculates a financial health score out of 100 based on:
    1. Savings Ratio (40 points)
    2. Overspending against limits (25 points)
    3. Budget Discipline / Limit coverage (20 points)
    4. Spending Trends (15 points)
    """
    if monthly_income <= 0:
        monthly_income = 50000.0  # Safe fallback default

    now = datetime.now()
    this_month_str = now.strftime("%Y-%m")
    
    # Calculate last month string
    if now.month == 1:
        last_month_str = f"{now.year - 1}-12"
    else:
        last_month_str = f"{now.year}-{str(now.month - 1).zfill(2)}"

    # Filter expenses
    this_month_expenses = [e for e in expenses if e.get("date", "").startswith(this_month_str)]
    last_month_expenses = [e for e in expenses if e.get("date", "").startswith(last_month_str)]

    this_month_total = sum(float(e["amount"]) for e in this_month_expenses)
    last_month_total = sum(float(e["amount"]) for e in last_month_expenses)

    # 1. Savings Ratio (Max 40 points)
    # Savings = Income - Expenses
    savings = max(0.0, monthly_income - this_month_total)
    savings_ratio = savings / monthly_income
    
    # 30% savings ratio or higher gives full 40 points, scaled linearly below 30%
    savings_score = min(40.0, (savings_ratio / 0.3) * 40.0)

    # 2. Overspending and Budget Limits (Max 25 points)
    # Group this month's expenses by category
    cat_spend = {}
    for e in this_month_expenses:
        cat = e["category"]
        cat_spend[cat] = cat_spend.get(cat, 0.0) + float(e["amount"])

    # Map limits for easy check
    limit_dict = {l["category"]: float(l["limit_amount"]) for l in limits}

    overspent_categories = 0
    limit_exceeded_amount = 0.0
    for cat, spend in cat_spend.items():
        if cat in limit_dict:
            limit = limit_dict[cat]
            if spend > limit:
                overspent_categories += 1
                limit_exceeded_amount += (spend - limit)

    # Calculate penalty
    if len(limit_dict) == 0:
        # No limits set, default to maximum if expenses are within income
        limit_adherence_score = 25.0 if this_month_total <= monthly_income else max(0.0, 25.0 - (this_month_total - monthly_income)/monthly_income * 25.0)
    else:
        # Deduct 8 points per overspent category, down to 0
        limit_adherence_score = max(0.0, 25.0 - (overspent_categories * 8.33))

    # 3. Budget Discipline (Max 20 points)
    # Rewarded for setting limits and tracking categories.
    # Award points based on having limits set for major categories.
    if len(limit_dict) >= 3:
        discipline_score = 20.0
    elif len(limit_dict) > 0:
        discipline_score = 10.0 + (len(limit_dict) * 3.33)
    else:
        discipline_score = 5.0  # Minimum points for tracking expenses

    # 4. Spending Trends (Max 15 points)
    # Awarded if spending this month is lower than or equal to last month, 
    # or if last month's spending was zero (new account)
    if last_month_total == 0:
        trends_score = 15.0
    else:
        diff_pct = (this_month_total - last_month_total) / last_month_total
        if diff_pct <= 0:
            trends_score = 15.0  # Reduced spending is good!
        elif diff_pct <= 0.1:
            trends_score = 10.0  # Slight increase (under 10%)
        else:
            trends_score = max(0.0, 15.0 - (diff_pct * 10))

    total_score = round(savings_score + limit_adherence_score + discipline_score + trends_score)
    total_score = min(100, max(0, total_score))

    # Health Grade & Color
    if total_score >= 80:
        grade = "Excellent"
        color = "#10B981"  # Success Green
        tips = [
            "Your savings ratio is excellent! Keep investing your surplus.",
            "You are demonstrating outstanding budget discipline."
        ]
    elif total_score >= 60:
        grade = "Good"
        color = "#60A5FA"  # Muted Blue
        tips = [
            "Consider setting strict limits on your top categories to save more.",
            "Try to reduce impulse shopping to boost your score to Excellent."
        ]
    elif total_score >= 40:
        grade = "Fair"
        color = "#F59E0B"  # Amber
        tips = [
            "Your spending is close to your total income. Try creating savings buffers first.",
            "Exceeded category limits are dragging down your score. Review limits."
        ]
    else:
        grade = "Critical"
        color = "#EF4444"  # Red
        tips = [
            "Warning: You are spending nearly all of or exceeding your monthly income.",
            "Create category budgets immediately and cut back on non-essential spending."
        ]

    return {
        "score": total_score,
        "grade": grade,
        "color": color,
        "breakdown": {
            "savings_score": round(savings_score, 1),
            "limit_adherence_score": round(limit_adherence_score, 1),
            "discipline_score": round(discipline_score, 1),
            "trends_score": round(trends_score, 1)
        },
        "tips": tips
    }
