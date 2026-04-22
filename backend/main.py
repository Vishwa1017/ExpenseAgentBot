from backend.routes.upload import router as upload_router
from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.include_router(upload_router)