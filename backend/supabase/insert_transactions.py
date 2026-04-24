from backend.supabase.client import supabase


def insert_transactions(user_id: int, transactions: list[dict], source_file: str):
    rows = []

    for tx in transactions:
        row = {
            "user_id": user_id,
            "transaction_date": tx["transaction_date"],
            "description": tx["description"],
            "amount": tx["amount"],
            "merchant": tx.get("merchant"),
            "transaction_type": tx["transaction_type"],
            "category": tx["category"],
            "account_type": tx["account_type"],
            "source_file": source_file,
        }
        rows.append(row)

    response = (
        supabase.table("transactions")
        .upsert(
            rows,
            on_conflict="user_id,transaction_date,description,amount,account_type"
        )
        .execute()
    )

    return response