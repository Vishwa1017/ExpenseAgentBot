from datetime import datetime

REQUIRED_FIELDS = ["transaction_date", "description", "amount", "category", "merchant"]


def is_valid_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_transaction(tx: dict) -> bool:
    for field in REQUIRED_FIELDS:
        if field not in tx:
            return False

    if not isinstance(tx["description"], str) or not tx["description"].strip():
        return False

    if not isinstance(tx["amount"], (int, float)):
        return False

    if not isinstance(tx["transaction_date"], str) or not is_valid_date(tx["transaction_date"]):
        return False

    return True


def validate_transactions(transactions: list[dict]) -> list[dict]:
    valid_transactions = []

    for tx in transactions:
        if validate_transaction(tx):
            valid_transactions.append(tx)

    return valid_transactions