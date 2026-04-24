from backend.routes.upload import router as upload_router
from backend.routes.analytics import router as summary_router

from fastapi import FastAPI
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.include_router(upload_router)
app.include_router(summary_router)