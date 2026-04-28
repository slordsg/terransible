from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import repo_root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SVC_", case_sensitive=False)

    data_dir: Path = repo_root() / "data"
    db_path: Path | None = None

    terraform_bin: str = "terraform"
    ansible_playbook_bin: str = "ansible-playbook"

    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None

    def resolved_db_path(self) -> Path:
        if self.db_path is not None:
            return self.db_path
        return self.data_dir / "svc.db"


settings = Settings()

