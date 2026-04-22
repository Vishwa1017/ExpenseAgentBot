import json
import os
import re
from typing import List, Dict, Any


from backend.services.pdf_parser.validator import validate_transactions
from langchain.chat_models import init_chat_model
from langchain_community.document_loaders import PyPDFLoader


def get_model(model_name: str = "gpt-5.2"):
    """Initialize and return the chat model."""
    return init_chat_model(model_name)


def load_pdf(file_path: str):
    """Load PDF pages as LangChain documents."""
    loader = PyPDFLoader(file_path)
    return loader.load()


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted PDF text."""
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def combine_pages(docs) -> str:
    """Combine all PDF pages into one cleaned string."""
    full_text = " ".join(doc.page_content for doc in docs)
    return clean_text(full_text)


def get_system_prompt() -> str:
    """Return the system prompt for transaction extraction."""
    return f"""
You are a financial data extraction assistant.

Your task is to read a bank or credit card statement and extract all transactions into structured JSON.

Return ONLY a valid JSON array.
Do not include markdown.
Do not include explanations.
Do not include code fences.

Each JSON object MUST contain:
- transaction_date
- description
- amount
- merchant
- transaction_type
- category
- account_type

-----------------------------------
FIELD DEFINITIONS:

transaction_date:
- Format: YYYY-MM-DD

amount:
- Negative for expenses
- Positive for income
- Transfers can be positive or negative depending on direction

account_type:
- "checking" → for bank account statements
- "credit" → for credit card statements

transaction_type (choose EXACTLY one):
- "income"
- "expense"
- "transfer"

-----------------------------------
CATEGORY RULES:

If transaction_type = "expense", choose ONLY from:
- Groceries
- Dining
- Transport
- Shopping
- Entertainment
- Utilities
- Rent
- Subscriptions
- Healthcare
- Insurance
- Education
- Travel
- Personal Care
- Gifts
- Bank Fees
- Other

If transaction_type = "income", choose ONLY from:
- Salary
- Freelance
- Refund
- Bonus
- Transfer In
- Other Income

If transaction_type = "transfer", choose ONLY from:
- Savings Transfer
- Credit Card Payment
- Internal Transfer

-----------------------------------
IMPORTANT RULES:

1. Expense = money leaving the user's system (spent on goods/services or sent to other people).

2. Transfer = money moved between the user's own accounts (checking, savings, credit card).

3. NEVER classify transfers as expenses.

-----------------------------------
TRANSFER DETECTION RULES:

Classify as "transfer" if the description includes:
- "Online Transfer"
- "Transfer to Deposit Account"
- "Internal Transfer"
- "Credit Card Payment"
- Movement between accounts (checking ↔ savings, checking ↔ credit)

-----------------------------------
E-TRANSFER RULES (VERY IMPORTANT):

For "e-Transfer":

- If sent to another person (friend, landlord, named individual):
  → transaction_type = "expense"
  → category = "Gifts" OR "Other" (choose best fit)

- If clearly internal (own account movement):
  → transaction_type = "transfer"
  → category = "Internal Transfer"

-----------------------------------
OTHER RULES:

4. Credit card purchases (Visa, POS, debit purchases):
   → transaction_type = "expense"

5. Credit card payments:
   → transaction_type = "transfer"
   → category = "Credit Card Payment"

6. Payroll, deposits, salary:
   → transaction_type = "income"

7. Infer merchant from description when possible.

8. Ignore:
   - headers
   - balances
   - totals
   - summaries
   - page numbers

9. Return an empty JSON array if no transactions are found.

-----------------------------------
EXAMPLE:

[
  {{
    "transaction_date": "2025-03-10",
    "description": "Walmart purchase",
    "amount": -45.67,
    "merchant": "Walmart",
    "transaction_type": "expense",
    "category": "Groceries",
    "account_type": "credit"
  }},
  {{
    "transaction_date": "2025-03-12",
    "description": "Payroll Deposit",
    "amount": 1500.00,
    "merchant": "Employer",
    "transaction_type": "income",
    "category": "Salary",
    "account_type": "checking"
  }},
  {{
    "transaction_date": "2025-03-15",
    "description": "Online transfer to savings",
    "amount": -500.00,
    "merchant": "RBC",
    "transaction_type": "transfer",
    "category": "Savings Transfer",
    "account_type": "checking"
  }}
]
""".strip()


def build_messages(statement_text: str) -> List[Dict[str, str]]:
    """Build messages for the LLM."""
    return [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": statement_text},
    ]


def extract_transactions(model, statement_text: str) -> List[Dict[str, Any]]:
    """Call the LLM and parse JSON transaction output."""
    messages = build_messages(statement_text)
    response = model.invoke(messages)
    raw_output = response.content.strip()

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned by model:\n{raw_output}") from e


def process_statement(file_path: str, model_name: str = "gpt-5.2"):
    """Full reusable pipeline: load PDF -> clean text -> extract transactions."""
    model = get_model(model_name)
    docs = load_pdf(file_path)
    statement_text = combine_pages(docs)
    transactions = extract_transactions(model, statement_text)
    validated_transactions = validate_transactions(transactions)
    return {
        "raw_count": len(transactions),
        "valid_count": len(validated_transactions),
        "transactions": validated_transactions
    }

def process_folder(folder_path: str, model_name: str = "gpt-5.2"):
    model = get_model(model_name)
    all_transactions = []

    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            print(f"Processing: {file_path}")

            docs = load_pdf(file_path)
            statement_text = combine_pages(docs)

            transactions = extract_transactions(model, statement_text)
            all_transactions.extend(transactions)

    return all_transactions