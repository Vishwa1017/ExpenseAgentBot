from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import tempfile
import os
from backend.services.pdf_parser.rbc_parser import process_statement
from backend.services.pdf_parser.validator import validate_transactions
from backend.supabase.insert_transactions import insert_transactions


router = APIRouter()

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name


        result = process_statement(temp_file_path)
        transactions = result["transactions"]
        db_response = insert_transactions(
    user_id=1,
    transactions=transactions,
    source_file=file.filename
)
        return {
    "message": "File processed successfully",
    "file_name": file.filename,
    "raw_count": result["raw_count"],
    "valid_count": result["valid_count"],
    "transactions": result["transactions"]
}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)