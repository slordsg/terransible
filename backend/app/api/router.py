from fastapi import APIRouter

from app.api.routes import environments, projects, runs, agent

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(environments.router, prefix="/envs", tags=["envs"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(agent.router, tags=["agent"])

