from fastapi import APIRouter
from backend.services.db.analytics_queries import *


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary/{user_id}/{year}/{month}")
def summary(user_id: int, year: int, month: int):
    return get_monthly_summary(user_id, year, month)


@router.get("/category/{user_id}/{year}/{month}")
def category(user_id: int, year: int, month: int):
    return get_category_breakdown(user_id, year, month)


@router.get("/merchants/{user_id}/{year}/{month}")
def merchants(user_id: int, year: int, month: int):
    return get_top_merchants(user_id, year, month)


