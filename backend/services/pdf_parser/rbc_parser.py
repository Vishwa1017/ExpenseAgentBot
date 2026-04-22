import json
import os
import re
from typing import List, Dict, Any

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

Your task is to read bank statement text and extract all transactions into structured JSON.

Return ONLY a valid JSON array.
Do not include markdown.
Do not include explanations.
Do not include code fences.

Each JSON object must contain:
- transaction_date
- description
- category
- amount
- merchant

Rules:
2. transaction_date must be in YYYY-MM-DD format.
3. amount must be negative for expenses and positive for income.
4. Infer merchant from description when possible.
5. Infer category from description when possible.
6. Ignore non-transaction rows like headers, balances, summaries, totals, and page numbers.
7. Return an empty JSON array if no transactions are found.

Example:
[
  {{
    "transaction_date": "2025-03-10",
    "description": "Walmart purchase",
    "category": "Groceries",
    "amount": -45.67,
    "merchant": "Walmart"
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
    return transactions

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