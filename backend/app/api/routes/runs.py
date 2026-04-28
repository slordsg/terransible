import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import get_db
from app.api.models import RunOut

router = APIRouter()


def _run_out(row: sqlite3.Row) -> RunOut:
    return RunOut(
        id=row["id"],
        env_id=row["env_id"],
        kind=row["kind"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        exit_code=row["exit_code"],
        log_path=row["log_path"],
        error=row["error"],
    )


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: str, conn: sqlite3.Connection = Depends(get_db)) -> RunOut:
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    return _run_out(row)


@router.get("/{run_id}/logs")
def get_run_logs(run_id: str, conn: sqlite3.Connection = Depends(get_db)) -> FileResponse:
    row = conn.execute("SELECT log_path FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    p = Path(row["log_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="log_not_found")
    return FileResponse(str(p), media_type="text/plain")

