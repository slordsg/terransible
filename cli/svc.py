import json
import os

import httpx
import typer

app = typer.Typer(no_args_is_help=True)


def api_base_url() -> str:
    return os.environ.get("SVC_API_URL", "http://127.0.0.1:8000")


def client() -> httpx.Client:
    return httpx.Client(base_url=api_base_url(), timeout=60.0)


projects_app = typer.Typer(no_args_is_help=True)
envs_app = typer.Typer(no_args_is_help=True)
tf_app = typer.Typer(no_args_is_help=True)
ansible_app = typer.Typer(no_args_is_help=True)
agent_app = typer.Typer(no_args_is_help=True)

app.add_typer(projects_app, name="projects")
app.add_typer(envs_app, name="envs")
app.add_typer(tf_app, name="tf")
app.add_typer(ansible_app, name="ansible")
app.add_typer(agent_app, name="agent")


@projects_app.command("create")
def projects_create(name: str) -> None:
    with client() as c:
        r = c.post("/projects", json={"name": name})
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@projects_app.command("get")
def projects_get(project_id: str) -> None:
    with client() as c:
        r = c.get(f"/projects/{project_id}")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@envs_app.command("create")
def envs_create(
    project_id: str,
    name: str,
    hosts_json: str = "[]",
    tf_vars_json: str = "{}",
    ansible_vars_json: str = "{}",
) -> None:
    with client() as c:
        r = c.post(
            "/envs",
            json={
                "project_id": project_id,
                "name": name,
                "hosts": json.loads(hosts_json),
                "tf_vars": json.loads(tf_vars_json),
                "ansible_vars": json.loads(ansible_vars_json),
            },
        )
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@envs_app.command("get")
def envs_get(env_id: str) -> None:
    with client() as c:
        r = c.get(f"/envs/{env_id}")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@envs_app.command("update")
def envs_update(
    env_id: str,
    hosts_json: str | None = None,
    tf_vars_json: str | None = None,
    ansible_vars_json: str | None = None,
) -> None:
    body: dict = {}
    if hosts_json is not None:
        body["hosts"] = json.loads(hosts_json)
    if tf_vars_json is not None:
        body["tf_vars"] = json.loads(tf_vars_json)
    if ansible_vars_json is not None:
        body["ansible_vars"] = json.loads(ansible_vars_json)
    with client() as c:
        r = c.put(f"/envs/{env_id}", json=body)
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@envs_app.command("generate")
def envs_generate(env_id: str) -> None:
    with client() as c:
        r = c.post(f"/envs/{env_id}/generate")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@tf_app.command("plan")
def tf_plan(env_id: str) -> None:
    with client() as c:
        r = c.post(f"/envs/{env_id}/terraform/plan")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@tf_app.command("apply")
def tf_apply(env_id: str) -> None:
    with client() as c:
        r = c.post(f"/envs/{env_id}/terraform/apply")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@ansible_app.command("run")
def ansible_run(env_id: str) -> None:
    with client() as c:
        r = c.post(f"/envs/{env_id}/ansible/run")
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


@app.command("run-logs")
def run_logs(run_id: str) -> None:
    with client() as c:
        r = c.get(f"/runs/{run_id}/logs")
        r.raise_for_status()
        typer.echo(r.text)


@agent_app.command("suggest")
def agent_suggest(env_id: str, prompt: str) -> None:
    with client() as c:
        r = c.post(f"/envs/{env_id}/agent/suggest", json={"prompt": prompt})
        r.raise_for_status()
        typer.echo(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()

