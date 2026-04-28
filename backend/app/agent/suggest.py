import json

from app.agent.provider import LLMProvider


class SuggestParseError(Exception):
    pass


def build_draft(project_name: str, env_name: str, env_hosts: list[dict], tf_vars: dict, ansible_vars: dict) -> dict:
    draft_tf = dict(tf_vars)
    draft_tf.setdefault("project_name", project_name)
    draft_tf.setdefault("environment_name", env_name)

    return {
        "hosts": env_hosts,
        "tf_vars": draft_tf,
        "ansible_vars": dict(ansible_vars),
    }


def suggest_from_llm(llm: LLMProvider, prompt: str, draft: dict) -> dict:
    system = (
        "你是一个配置生成助手。你必须只输出严格 JSON（不要 Markdown）。"
        "输出必须是对象，包含 hosts(数组), tf_vars(对象), ansible_vars(对象)。"
        "不要添加额外字段。"
    )
    user = (
        "需求描述:\n"
        f"{prompt}\n\n"
        "当前草案 JSON:\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        "请返回更新后的 JSON。"
    )
    content = llm.chat_json(system=system, user=user)
    try:
        obj = json.loads(content)
    except json.JSONDecodeError as e:
        raise SuggestParseError(str(e))

    if not isinstance(obj, dict):
        raise SuggestParseError("not_object")
    for k in ("hosts", "tf_vars", "ansible_vars"):
        if k not in obj:
            raise SuggestParseError(f"missing_{k}")
    return obj

