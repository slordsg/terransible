import sqlite3

from app.core.clock import now_utc_iso


class EnvLockedError(Exception):
    pass


def lock_env(conn: sqlite3.Connection, env_id: str, run_id: str) -> None:
    conn.execute("BEGIN IMMEDIATE;")
    row = conn.execute(
        "SELECT locked_by_run_id FROM tf_state_meta WHERE env_id = ?",
        (env_id,),
    ).fetchone()
    if row is None:
        raise EnvLockedError("tf_state_meta_not_initialized")
    if row["locked_by_run_id"] is not None:
        raise EnvLockedError("env_locked")
    conn.execute(
        "UPDATE tf_state_meta SET locked_by_run_id = ?, locked_at = ? WHERE env_id = ?",
        (run_id, now_utc_iso(), env_id),
    )


def unlock_env(conn: sqlite3.Connection, env_id: str, run_id: str) -> None:
    conn.execute("BEGIN IMMEDIATE;")
    row = conn.execute(
        "SELECT locked_by_run_id FROM tf_state_meta WHERE env_id = ?",
        (env_id,),
    ).fetchone()
    if row is None:
        return
    if row["locked_by_run_id"] != run_id:
        return
    conn.execute(
        "UPDATE tf_state_meta SET locked_by_run_id = NULL, locked_at = NULL WHERE env_id = ?",
        (env_id,),
    )

