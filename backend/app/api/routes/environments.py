import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_db
from app.api.models import EnvCreate, EnvOut, EnvUpdate, RunOut
from app.core.clock import now_utc_iso
from app.core.settings import settings
from app.core.workspaces import ansible_workdir, env_root_dir, run_logs_dir, terraform_workdir
from app.db import repo
from app.terraform.generator import write_terraform_dir
from app.ansible.generator import write_ansible_dir
from app.core.executor import run_cmd
from app.core.locking import EnvLockedError, lock_env, unlock_env

router = APIRouter()


def _env_out(e: repo.Environment) -> EnvOut:
    return EnvOut(
        id=e.id,
        project_id=e.project_id,
        name=e.name,
        hosts=e.hosts(),
        tf_vars=e.tf_vars(),
        ansible_vars=e.ansible_vars(),
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


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


@router.post("", response_model=EnvOut)
def create_env(payload: EnvCreate, conn: sqlite3.Connection = Depends(get_db)) -> EnvOut:
    if repo.get_project(conn, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="project_not_found")
    e = repo.create_env(conn, payload.project_id, payload.name, payload.hosts, payload.tf_vars, payload.ansible_vars)

    tf_dir = terraform_workdir(e.project_id, e.name)
    state_path = tf_dir / "terraform.tfstate"
    repo.ensure_tf_state_meta(conn, e.id, str(tf_dir), str(state_path))

    conn.commit()
    return _env_out(e)


@router.get("/{env_id}", response_model=EnvOut)
def get_env(env_id: str, conn: sqlite3.Connection = Depends(get_db)) -> EnvOut:
    e = repo.get_env(conn, env_id)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")
    return _env_out(e)


@router.put("/{env_id}", response_model=EnvOut)
def update_env(env_id: str, payload: EnvUpdate, conn: sqlite3.Connection = Depends(get_db)) -> EnvOut:
    e = repo.update_env(conn, env_id, payload.hosts, payload.tf_vars, payload.ansible_vars)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")
    conn.commit()
    return _env_out(e)


@router.post("/{env_id}/generate", response_model=RunOut)
def generate(env_id: str, conn: sqlite3.Connection = Depends(get_db)) -> RunOut:
    e = repo.get_env(conn, env_id)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")

    logs_dir = run_logs_dir()
    log_path = logs_dir / f"{env_id}-generate.log"
    run_id = repo.create_run(conn, env_id, kind="generate", log_path=str(log_path))

    try:
        lock_env(conn, env_id, run_id)
    except EnvLockedError as ex:
        repo.finish_run(conn, run_id, status="failed", exit_code=None, error=str(ex))
        raise HTTPException(status_code=409, detail="env_locked")

    try:
        tf_dir = terraform_workdir(e.project_id, e.name)
        state_path = tf_dir / "terraform.tfstate"
        repo.ensure_tf_state_meta(conn, e.id, str(tf_dir), str(state_path))
        tf_written = write_terraform_dir(tf_dir, e.tf_vars(), state_path)

        ans_dir = ansible_workdir(e.project_id, e.name)
        ans_written = write_ansible_dir(ans_dir, e.hosts(), e.ansible_vars())

        root = env_root_dir(e.project_id, e.name)
        for p in tf_written:
            repo.add_artifact(conn, env_id=e.id, run_id=run_id, rel_path=str(p.relative_to(root)), kind="terraform")
        for p in ans_written:
            repo.add_artifact(conn, env_id=e.id, run_id=run_id, rel_path=str(p.relative_to(root)), kind="ansible")

        repo.finish_run(conn, run_id, status="succeeded", exit_code=0, error=None)
    finally:
        unlock_env(conn, env_id, run_id)

    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row is not None
    return _run_out(row)


def _run_tf(conn: sqlite3.Connection, env_id: str, kind: str, args: list[list[str]]) -> RunOut:
    e = repo.get_env(conn, env_id)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")

    tf_dir = terraform_workdir(e.project_id, e.name)
    state_path = tf_dir / "terraform.tfstate"
    repo.ensure_tf_state_meta(conn, e.id, str(tf_dir), str(state_path))

    logs_dir = run_logs_dir()
    log_path = logs_dir / f"{env_id}-{kind}.log"
    run_id = repo.create_run(conn, env_id, kind=f"terraform_{kind}", log_path=str(log_path))

    try:
        lock_env(conn, env_id, run_id)
    except EnvLockedError as ex:
        repo.finish_run(conn, run_id, status="failed", exit_code=None, error=str(ex))
        raise HTTPException(status_code=409, detail="env_locked")

    try:
        last_result = None
        for i, a in enumerate(args):
            last_result = run_cmd(
                [settings.terraform_bin, *a],
                cwd=tf_dir,
                log_path=Path(log_path),
                append=(i != 0),
            )
            if last_result.exit_code != 0:
                break

        assert last_result is not None
        status = "succeeded" if last_result.exit_code == 0 else "failed"
        repo.finish_run(conn, run_id, status=status, exit_code=last_result.exit_code, error=last_result.error)
        conn.execute(
            f"UPDATE tf_state_meta SET last_{kind}_at = ?, last_exit_code = ?, last_error = ? WHERE env_id = ?",
            (now_utc_iso(), last_result.exit_code, last_result.error, env_id),
        )
    finally:
        unlock_env(conn, env_id, run_id)

    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row is not None
    return _run_out(row)


@router.post("/{env_id}/terraform/plan", response_model=RunOut)
def terraform_plan(env_id: str, conn: sqlite3.Connection = Depends(get_db)) -> RunOut:
    return _run_tf(
        conn,
        env_id,
        "plan",
        [
            ["init", "-input=false", "-no-color", "-upgrade"],
            ["plan", "-input=false", "-no-color"],
        ],
    )


@router.post("/{env_id}/terraform/apply", response_model=RunOut)
def terraform_apply(env_id: str, conn: sqlite3.Connection = Depends(get_db)) -> RunOut:
    return _run_tf(
        conn,
        env_id,
        "apply",
        [
            ["init", "-input=false", "-no-color", "-upgrade"],
            ["apply", "-auto-approve", "-input=false", "-no-color"],
        ],
    )


@router.post("/{env_id}/ansible/run", response_model=RunOut)
def ansible_run(env_id: str, conn: sqlite3.Connection = Depends(get_db)) -> RunOut:
    e = repo.get_env(conn, env_id)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")

    ans_dir = ansible_workdir(e.project_id, e.name)
    inv_path = ans_dir / "inventory.ini"
    site_path = ans_dir / "site.yml"

    logs_dir = run_logs_dir()
    log_path = logs_dir / f"{env_id}-ansible-run.log"
    run_id = repo.create_run(conn, env_id, kind="ansible_run", log_path=str(log_path))

    try:
        lock_env(conn, env_id, run_id)
    except EnvLockedError as ex:
        repo.finish_run(conn, run_id, status="failed", exit_code=None, error=str(ex))
        raise HTTPException(status_code=409, detail="env_locked")

    try:
        args = [
            settings.ansible_playbook_bin,
            "-i",
            str(inv_path),
            str(site_path),
        ]
        result = run_cmd(args, cwd=ans_dir, log_path=Path(log_path))
        status = "succeeded" if result.exit_code == 0 else "failed"
        repo.finish_run(conn, run_id, status=status, exit_code=result.exit_code, error=result.error)
    finally:
        unlock_env(conn, env_id, run_id)

    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    assert row is not None
    return _run_out(row)

