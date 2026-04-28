from fastapi import APIRouter, Depends, HTTPException
import sqlite3

from app.api.deps import get_db
from app.api.models import ProjectCreate, ProjectOut
from app.db import repo

router = APIRouter()


@router.post("", response_model=ProjectOut)
def create_project(payload: ProjectCreate, conn: sqlite3.Connection = Depends(get_db)) -> ProjectOut:
    p = repo.create_project(conn, payload.name)
    conn.commit()
    return ProjectOut(id=p.id, name=p.name, created_at=p.created_at)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, conn: sqlite3.Connection = Depends(get_db)) -> ProjectOut:
    p = repo.get_project(conn, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    return ProjectOut(id=p.id, name=p.name, created_at=p.created_at)

