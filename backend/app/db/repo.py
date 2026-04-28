import json
import sqlite3
import uuid
from dataclasses import dataclass

from app.core.clock import now_utc_iso


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    created_at: str


@dataclass(frozen=True)
class Environment:
    id: str
    project_id: str
    name: str
    hosts_json: str
    tf_vars_json: str
    ansible_vars_json: str
    created_at: str
    updated_at: str

    def hosts(self) -> list[dict]:
        return json.loads(self.hosts_json)

    def tf_vars(self) -> dict:
        return json.loads(self.tf_vars_json)

    def ansible_vars(self) -> dict:
        return json.loads(self.ansible_vars_json)


def create_project(conn: sqlite3.Connection, name: str) -> Project:
    pid = str(uuid.uuid4())
    created_at = now_utc_iso()
    conn.execute(
        "INSERT INTO projects(id, name, created_at) VALUES (?, ?, ?)",
        (pid, name, created_at),
    )
    return Project(id=pid, name=name, created_at=created_at)


def get_project(conn: sqlite3.Connection, project_id: str) -> Project | None:
    row = conn.execute(
        "SELECT id, name, created_at FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        return None
    return Project(id=row["id"], name=row["name"], created_at=row["created_at"])


def create_env(
    conn: sqlite3.Connection,
    project_id: str,
    name: str,
    hosts: list[dict],
    tf_vars: dict,
    ansible_vars: dict,
) -> Environment:
    eid = str(uuid.uuid4())
    now = now_utc_iso()
    conn.execute(
        """
        INSERT INTO environments(
          id, project_id, name, hosts_json, tf_vars_json, ansible_vars_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            eid,
            project_id,
            name,
            json.dumps(hosts, ensure_ascii=False),
            json.dumps(tf_vars, ensure_ascii=False),
            json.dumps(ansible_vars, ensure_ascii=False),
            now,
            now,
        ),
    )
    return get_env(conn, eid)


def update_env(
    conn: sqlite3.Connection,
    env_id: str,
    hosts: list[dict] | None,
    tf_vars: dict | None,
    ansible_vars: dict | None,
) -> Environment | None:
    existing = get_env(conn, env_id)
    if existing is None:
        return None
    new_hosts_json = existing.hosts_json if hosts is None else json.dumps(hosts, ensure_ascii=False)
    new_tf_vars_json = existing.tf_vars_json if tf_vars is None else json.dumps(tf_vars, ensure_ascii=False)
    new_ansible_vars_json = (
        existing.ansible_vars_json
        if ansible_vars is None
        else json.dumps(ansible_vars, ensure_ascii=False)
    )
    now = now_utc_iso()
    conn.execute(
        """
        UPDATE environments
        SET hosts_json = ?, tf_vars_json = ?, ansible_vars_json = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_hosts_json, new_tf_vars_json, new_ansible_vars_json, now, env_id),
    )
    return get_env(conn, env_id)


def get_env(conn: sqlite3.Connection, env_id: str) -> Environment | None:
    row = conn.execute(
        """
        SELECT id, project_id, name, hosts_json, tf_vars_json, ansible_vars_json, created_at, updated_at
        FROM environments
        WHERE id = ?
        """,
        (env_id,),
    ).fetchone()
    if row is None:
        return None
    return Environment(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        hosts_json=row["hosts_json"],
        tf_vars_json=row["tf_vars_json"],
        ansible_vars_json=row["ansible_vars_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def ensure_tf_state_meta(conn: sqlite3.Connection, env_id: str, workdir: str, state_path: str) -> None:
    conn.execute(
        """
        INSERT INTO tf_state_meta(env_id, workdir, state_path)
        VALUES (?, ?, ?)
        ON CONFLICT(env_id) DO UPDATE SET workdir = excluded.workdir, state_path = excluded.state_path
        """,
        (env_id, workdir, state_path),
    )


def create_run(
    conn: sqlite3.Connection,
    env_id: str,
    kind: str,
    log_path: str,
) -> str:
    run_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO runs(id, env_id, kind, status, started_at, log_path)
        VALUES (?, ?, ?, 'running', ?, ?)
        """,
        (run_id, env_id, kind, now_utc_iso(), log_path),
    )
    return run_id


def finish_run(
    conn: sqlite3.Connection,
    run_id: str,
    status: str,
    exit_code: int | None,
    error: str | None,
) -> None:
    conn.execute(
        """
        UPDATE runs
        SET status = ?, finished_at = ?, exit_code = ?, error = ?
        WHERE id = ?
        """,
        (status, now_utc_iso(), exit_code, error, run_id),
    )


def add_artifact(
    conn: sqlite3.Connection,
    env_id: str,
    run_id: str,
    rel_path: str,
    kind: str,
) -> str:
    aid = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO artifacts(id, env_id, run_id, rel_path, kind, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (aid, env_id, run_id, rel_path, kind, now_utc_iso()),
    )
    return aid

