import json
import os

import httpx


def main() -> None:
    base_url = os.environ.get("SVC_API_URL", "http://127.0.0.1:8000")
    c = httpx.Client(base_url=base_url, timeout=60.0)

    p = c.post("/projects", json={"name": "smoke"}).json()
    env = c.post(
        "/envs",
        json={
            "project_id": p["id"],
            "name": "dev",
            "hosts": [],
            "tf_vars": {"project_name": "smoke", "environment_name": "dev"},
            "ansible_vars": {},
        },
    ).json()

    gen = c.post(f"/envs/{env['id']}/generate").json()
    plan = c.post(f"/envs/{env['id']}/terraform/plan").json()

    print(json.dumps({"project": p, "env": env, "generate_run": gen, "plan_run": plan}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

