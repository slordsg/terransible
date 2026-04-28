import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.agent.provider import LLMNotConfiguredError, LLMProvider
from app.agent.suggest import SuggestParseError, build_draft, suggest_from_llm
from app.api.deps import get_db
from app.api.models import AgentSuggestIn, AgentSuggestOut
from app.core.settings import settings
from app.db import repo

router = APIRouter()


def _llm() -> LLMProvider:
    if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
        raise LLMNotConfiguredError("llm_not_configured")
    return LLMProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


@router.post("/envs/{env_id}/agent/suggest", response_model=AgentSuggestOut)
def agent_suggest(
    env_id: str,
    payload: AgentSuggestIn,
    conn: sqlite3.Connection = Depends(get_db),
) -> AgentSuggestOut:
    e = repo.get_env(conn, env_id)
    if e is None:
        raise HTTPException(status_code=404, detail="env_not_found")

    try:
        llm = _llm()
    except LLMNotConfiguredError:
        raise HTTPException(status_code=400, detail="llm_not_configured")

    p = repo.get_project(conn, e.project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="project_not_found")

    draft = build_draft(
        project_name=p.name,
        env_name=e.name,
        env_hosts=e.hosts(),
        tf_vars=e.tf_vars(),
        ansible_vars=e.ansible_vars(),
    )
    try:
        obj = suggest_from_llm(llm, payload.prompt, draft)
    except SuggestParseError as ex:
        raise HTTPException(status_code=502, detail=f"agent_invalid_json:{ex}")

    return AgentSuggestOut(hosts=obj["hosts"], tf_vars=obj["tf_vars"], ansible_vars=obj["ansible_vars"])

