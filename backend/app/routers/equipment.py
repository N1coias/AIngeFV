from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Inverter, Module
from backend.app.schemas import InverterIn, ModuleIn

router = APIRouter()


@router.post("/modules")
def upsert_module(
    payload: ModuleIn,
    db: Session = Depends(get_db),
) -> dict:
    row = (
        db.query(Module)
        .filter(
            Module.manufacturer == payload.manufacturer,
            Module.family == payload.family,
            Module.model == payload.model,
            Module.pmax_w == payload.pmax_w,
        )
        .one_or_none()
    )

    created = row is None
    if row is None:
        row = Module()

    for key, value in payload.model_dump().items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "created": created,
        "model": row.model,
    }


@router.get("/modules")
def list_modules(
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        {
            column.name: getattr(row, column.name)
            for column in Module.__table__.columns
            if column.name not in {"created_at", "updated_at"}
        }
        for row in (
            db.query(Module)
            .order_by(
                Module.manufacturer,
                Module.family,
                Module.pmax_w,
            )
            .all()
        )
    ]


@router.post("/inverters")
def upsert_inverter(
    payload: InverterIn,
    db: Session = Depends(get_db),
) -> dict:
    row = (
        db.query(Inverter)
        .filter(Inverter.model == payload.model)
        .one_or_none()
    )

    created = row is None
    if row is None:
        row = Inverter()

    for key, value in payload.model_dump().items():
        setattr(row, key, value)

    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "created": created,
        "model": row.model,
    }


@router.get("/inverters")
def list_inverters(
    db: Session = Depends(get_db),
) -> list[dict]:
    return [
        {
            column.name: getattr(row, column.name)
            for column in Inverter.__table__.columns
            if column.name not in {"created_at", "updated_at"}
        }
        for row in (
            db.query(Inverter)
            .order_by(Inverter.manufacturer, Inverter.model)
            .all()
        )
    ]
