from sqlalchemy import text

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db

router = APIRouter()


@router.get("")
def health() -> dict:
    return {
        "status": "ok",
        "version": "1.0.3",
    }


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            503,
            "La API funciona, pero la base de datos no está disponible.",
        ) from exc

    return {
        "status": "ready",
        "database": "ok",
    }
