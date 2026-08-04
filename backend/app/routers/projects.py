from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Project
from backend.app.schemas import ProjectIn

router = APIRouter()


@router.post("")
def save_project(payload: ProjectIn, db: Session = Depends(get_db)) -> dict:
    row = Project(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


@router.get("")
def list_projects(db: Session = Depends(get_db)) -> list[dict]:
    return [
        {
            "id": row.id,
            "name": row.name,
            "client": row.client,
            "location": row.location,
            "roof_type": row.roof_type,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in db.query(Project).order_by(Project.id.desc()).all()
    ]
