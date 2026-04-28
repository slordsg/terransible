import json
from pathlib import Path

from jinja2 import Environment as JinjaEnv
from jinja2 import FileSystemLoader

from app.core.paths import templates_root


def _jinja() -> JinjaEnv:
    loader = FileSystemLoader(str(templates_root() / "ansible"))
    env = JinjaEnv(loader=loader, autoescape=False, keep_trailing_newline=True)
    return env


def write_ansible_dir(workdir: Path, hosts: list[dict], ansible_vars: dict) -> list[Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    (workdir / "group_vars").mkdir(parents=True, exist_ok=True)

    j = _jinja()
    inventory_content = j.get_template("basic/inventory.ini.j2").render(hosts=hosts)
    inv_path = workdir / "inventory.ini"
    inv_path.write_text(inventory_content, encoding="utf-8")
    written.append(inv_path)

    site_content = j.get_template("basic/site.yml.j2").render()
    site_path = workdir / "site.yml"
    site_path.write_text(site_content, encoding="utf-8")
    written.append(site_path)

    all_vars_path = workdir / "group_vars" / "all.json"
    all_vars_path.write_text(json.dumps(ansible_vars, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(all_vars_path)

    return written

