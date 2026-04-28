## Terraform + Ansible 资源配置服务

本项目提供一个本地“服务器资源配置服务”，支持：

- 以 **Project/Environment** 为单位管理配置（元数据存 SQLite）
- 生成 Terraform 配置目录（本地 backend/state，state 元信息写入 SQLite）
- 生成 Ansible 配置目录（inventory/group_vars/site.yml），并可执行系统初始化
- 提供 **HTTP API（FastAPI）** + **CLI（Typer）**
- 提供 **agent**：模板/规则生成结构化草案 + LLM 辅助补全（未配置 LLM 时 agent 接口会报错）

## 快速开始

### 1) 安装依赖

在 `backend` 目录安装：

```bash
python -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
```

### 2) 启动 API

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

浏览 `http://127.0.0.1:8000/docs`。

### 3) 使用 CLI

CLI 位于 `cli`，默认通过 HTTP 调用 API。

## 配置

环境变量（API/CLI 通用）：

- `SVC_DATA_DIR`：数据目录（默认 `./data`）
- `SVC_DB_PATH`：SQLite 路径（默认 `${SVC_DATA_DIR}/svc.db`）
- `SVC_TERRAFORM_BIN`：terraform 可执行文件名/路径（默认 `terraform`）
- `SVC_ANSIBLE_PLAYBOOK_BIN`：ansible-playbook 可执行文件名/路径（默认 `ansible-playbook`）
- `SVC_LLM_BASE_URL` / `SVC_LLM_API_KEY` / `SVC_LLM_MODEL`：agent LLM 配置（不配置则 agent 端点报错）

