from backend.supabase.client import supabase


def _get_date_range(year: int, month: int):
    """
    Compute the start and end date for a given month.

    Args:
        year (int): Year (e.g., 2026)
        month (int): Month (1-12)

    Returns:
        tuple: (start_date, end_date) in YYYY-MM-DD format
    """
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year + 1}-01-01" if month == 12 else f"{year}-{month + 1:02d}-01"
    return start_date, end_date


def get_monthly_summary(user_id: int, year: int, month: int):
    """
    Calculate a financial summary for a given user and month.

    Includes:
    - total expense
    - total income
    - total transfers
    - transaction count
    - net flow

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month

    Returns:
        dict: Summary of financial metrics
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("amount, transaction_type")
        .eq("user_id", user_id)
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []

    total_expense = sum(abs(float(tx["amount"])) for tx in rows if tx["transaction_type"] == "expense")
    total_income = sum(float(tx["amount"]) for tx in rows if tx["transaction_type"] == "income")
    total_transfer = sum(abs(float(tx["amount"])) for tx in rows if tx["transaction_type"] == "transfer")

    return {
        "user_id": user_id,
        "year": year,
        "month": month,
        "total_expense": round(total_expense, 2),
        "total_income": round(total_income, 2),
        "total_transfer": round(total_transfer, 2),
        "transaction_count": len(rows),
        "net_flow": round(total_income - total_expense, 2),
    }


def get_category_breakdown(user_id: int, year: int, month: int):
    """
    Get spending grouped by category for a given month.

    Only includes expense transactions.

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month

    Returns:
        list[dict]: Sorted list of categories with total spend
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("category, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []
    category_totals = {}

    for tx in rows:
        category = tx["category"] or "Other"
        amount = abs(float(tx["amount"]))
        category_totals[category] = category_totals.get(category, 0) + amount

    result = [
        {"category": category, "total_spent": round(total, 2)}
        for category, total in category_totals.items()
    ]

    result.sort(key=lambda x: x["total_spent"], reverse=True)
    return result


def get_top_merchants(user_id: int, year: int, month: int, limit: int = 5):
    """
    Get top merchants by spending for a given month.

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month
        limit (int): Number of merchants to return

    Returns:
        list[dict]: Top merchants sorted by total spend
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("merchant, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []
    merchant_totals = {}

    for tx in rows:
        merchant = tx["merchant"] or "Unknown"
        amount = abs(float(tx["amount"]))
        merchant_totals[merchant] = merchant_totals.get(merchant, 0) + amount

    result = [
        {"merchant": merchant, "total_spent": round(total, 2)}
        for merchant, total in merchant_totals.items()
    ]

    result.sort(key=lambda x: x["total_spent"], reverse=True)
    return result[:limit]


def get_daily_spending_trend(user_id: int, year: int, month: int):
    """
    Get daily spending totals for a given month.

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month

    Returns:
        list[dict]: Daily spending trend sorted by date
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("transaction_date, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []
    daily_totals = {}

    for tx in rows:
        day = tx["transaction_date"]
        amount = abs(float(tx["amount"]))
        daily_totals[day] = daily_totals.get(day, 0) + amount

    result = [
        {"transaction_date": day, "total_spent": round(total, 2)}
        for day, total in daily_totals.items()
    ]

    result.sort(key=lambda x: x["transaction_date"])
    return result


def get_largest_expenses(user_id: int, year: int, month: int, limit: int = 5):
    """
    Get largest individual expense transactions.

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month
        limit (int): Number of results

    Returns:
        list[dict]: Largest expenses sorted by amount
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("transaction_date, merchant, description, category, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []

    result = [
        {
            "transaction_date": tx["transaction_date"],
            "merchant": tx["merchant"] or "Unknown",
            "description": tx["description"],
            "category": tx["category"],
            "amount": round(abs(float(tx["amount"])), 2),
        }
        for tx in rows
    ]

    result.sort(key=lambda x: x["amount"], reverse=True)
    return result[:limit]


def get_income_sources(user_id: int, year: int, month: int):
    """
    Get income grouped by source (merchant).

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month

    Returns:
        list[dict]: Income sources sorted by total income
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("merchant, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "income")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []
    income_totals = {}

    for tx in rows:
        merchant = tx["merchant"] or "Unknown"
        amount = float(tx["amount"])
        income_totals[merchant] = income_totals.get(merchant, 0) + amount

    result = [
        {"merchant": merchant, "total_income": round(total, 2)}
        for merchant, total in income_totals.items()
    ]

    result.sort(key=lambda x: x["total_income"], reverse=True)
    return result


def get_spending_by_account_type(user_id: int, year: int, month: int):
    """
    Get spending grouped by account type (checking vs credit).

    Args:
        user_id (int): User ID
        year (int): Year
        month (int): Month

    Returns:
        list[dict]: Spending totals per account type
    """
    start_date, end_date = _get_date_range(year, month)

    response = (
        supabase.table("transactions")
        .select("account_type, amount")
        .eq("user_id", user_id)
        .eq("transaction_type", "expense")
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []
    totals = {}

    for tx in rows:
        account_type = tx["account_type"]
        amount = abs(float(tx["amount"]))
        totals[account_type] = totals.get(account_type, 0) + amount

    result = [
        {"account_type": account_type, "total_spent": round(total, 2)}
        for account_type, total in totals.items()
    ]

    result.sort(key=lambda x: x["total_spent"], reverse=True)
    return result


def get_monthly_trend(user_id: int):
    """
    Get month-over-month spending and income trend.

    Args:
        user_id (int): User ID

    Returns:
        list[dict]: Monthly totals for income and expenses
    """
    response = (
        supabase.table("transactions")
        .select("transaction_date, amount, transaction_type")
        .eq("user_id", user_id)
        .execute()
    )

    rows = response.data or []
    monthly = {}

    for tx in rows:
        month = tx["transaction_date"][:7]
        tx_type = tx["transaction_type"]
        amount = float(tx["amount"])

        if month not in monthly:
            monthly[month] = {"month": month, "total_expense": 0, "total_income": 0}

        if tx_type == "expense":
            monthly[month]["total_expense"] += abs(amount)
        elif tx_type == "income":
            monthly[month]["total_income"] += amount

    result = list(monthly.values())
    result.sort(key=lambda x: x["month"])

    for row in result:
        row["total_expense"] = round(row["total_expense"], 2)
        row["total_income"] = round(row["total_income"], 2)

    return result