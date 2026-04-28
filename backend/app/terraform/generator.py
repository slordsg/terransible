import json
from pathlib import Path

from jinja2 import Environment as JinjaEnv
from jinja2 import FileSystemLoader

from app.core.paths import templates_root


def _jinja() -> JinjaEnv:
    loader = FileSystemLoader(str(templates_root() / "terraform"))
    env = JinjaEnv(loader=loader, autoescape=False, keep_trailing_newline=True)
    return env


def write_terraform_dir(workdir: Path, tf_vars: dict, state_path: Path) -> list[Path]:
    workdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    j = _jinja()
    files = {
        "main.tf": "basic/main.tf.j2",
        "variables.tf": "basic/variables.tf.j2",
        "outputs.tf": "basic/outputs.tf.j2",
        "backend.tf": "basic/backend.tf.j2",
    }
    for out_name, tpl_name in files.items():
        content = j.get_template(tpl_name).render(state_path=str(state_path).replace("\\", "/"))
        out_path = workdir / out_name
        out_path.write_text(content, encoding="utf-8")
        written.append(out_path)

    tfvars_path = workdir / "terraform.tfvars.json"
    tfvars_path.write_text(json.dumps(tf_vars, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(tfvars_path)

    return written

