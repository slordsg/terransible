from app.db.conn import db


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS environments (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  hosts_json TEXT NOT NULL,
  tf_vars_json TEXT NOT NULL,
  ansible_vars_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_env_project_name ON environments(project_id, name);

CREATE TABLE IF NOT EXISTS tf_state_meta (
  env_id TEXT PRIMARY KEY,
  workdir TEXT NOT NULL,
  state_path TEXT NOT NULL,
  locked_by_run_id TEXT,
  locked_at TEXT,
  last_init_at TEXT,
  last_plan_at TEXT,
  last_apply_at TEXT,
  last_destroy_at TEXT,
  last_exit_code INTEGER,
  last_error TEXT,
  FOREIGN KEY(env_id) REFERENCES environments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  env_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  exit_code INTEGER,
  log_path TEXT NOT NULL,
  error TEXT,
  FOREIGN KEY(env_id) REFERENCES environments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_env_started ON runs(env_id, started_at);

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  env_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  rel_path TEXT NOT NULL,
  kind TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(env_id) REFERENCES environments(id) ON DELETE CASCADE,
  FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id);
"""


def migrate() -> None:
    with db() as conn:
        conn.executescript(SCHEMA_SQL)


