from backend.supabase.client import supabase


def get_monthly_summary(user_id: int, year: int, month: int):
    start_date = f"{year}-{month:02d}-01"

    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    response = (
        supabase.table("transactions")
        .select("amount, transaction_type")
        .eq("user_id", user_id)
        .gte("transaction_date", start_date)
        .lt("transaction_date", end_date)
        .execute()
    )

    rows = response.data or []

    total_expense = 0
    total_income = 0
    total_transfer = 0

    for tx in rows:
        amount = float(tx["amount"])
        tx_type = tx["transaction_type"]

        if tx_type == "expense":
            total_expense += abs(amount)
        elif tx_type == "income":
            total_income += amount
        elif tx_type == "transfer":
            total_transfer += abs(amount)

    return {
        "user_id": user_id,
        "year": year,
        "month": month,
        "total_expense": round(total_expense, 2),
        "total_income": round(total_income, 2),
        "total_transfer": round(total_transfer, 2),
        "transaction_count": len(rows),
        "net_flow": round(total_income - total_expense, 2)
    }