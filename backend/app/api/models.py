from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectOut(BaseModel):
    id: str
    name: str
    created_at: str


class EnvCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=1, max_length=200)
    hosts: list[dict] = Field(default_factory=list)
    tf_vars: dict = Field(default_factory=dict)
    ansible_vars: dict = Field(default_factory=dict)


class EnvUpdate(BaseModel):
    hosts: list[dict] | None = None
    tf_vars: dict | None = None
    ansible_vars: dict | None = None


class EnvOut(BaseModel):
    id: str
    project_id: str
    name: str
    hosts: list[dict]
    tf_vars: dict
    ansible_vars: dict
    created_at: str
    updated_at: str


class RunOut(BaseModel):
    id: str
    env_id: str
    kind: str
    status: str
    started_at: str
    finished_at: str | None
    exit_code: int | None
    log_path: str
    error: str | None


class AgentSuggestIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)


class AgentSuggestOut(BaseModel):
    hosts: list[dict]
    tf_vars: dict
    ansible_vars: dict

