from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import tempfile
import os
from backend.services.pdf_parser.rbc_parser import process_statement
from backend.services.pdf_parser.validator import validate_transactions


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

        transactions = process_statement(temp_file_path)
        validated_transactions = validate_transactions(transactions)

        return {
            "message": "File processed successfully",
            "file_name": file.filename,
            "count": len(validated_transactions),
            "transactions": validated_transactions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)