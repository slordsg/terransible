from pathlib import Path

from app.core.settings import settings


def env_root_dir(project_id: str, env_name: str) -> Path:
    return settings.data_dir / "workspaces" / project_id / env_name


def terraform_workdir(project_id: str, env_name: str) -> Path:
    return env_root_dir(project_id, env_name) / "terraform"


def ansible_workdir(project_id: str, env_name: str) -> Path:
    return env_root_dir(project_id, env_name) / "ansible"


def run_logs_dir() -> Path:
    return settings.data_dir / "runs"

