# Contributing

Thanks for helping make `claude-multiengine-router` safer and easier to install.

## Scope

This project installs Claude Code routing assets, proxy agents, and a Grok MCP server. Please keep changes portable across macOS, Linux, and Windows, and keep installer tests away from real user profiles.

## Run Checks

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r mcp-servers/grok-mcp/requirements.txt
bash -n install.sh uninstall.sh tests/test_install_temp_home.sh tests/test_uninstall_temp_home.sh
bash tests/test_install_temp_home.sh
bash tests/test_uninstall_temp_home.sh
python3 tests/test_python_installer.py
python3 -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'
python3 tests/ci_install_dry_run.py
python3 tests/private_leak_gate.py .
```

Windows contributors can run the Python checks with `python` and the wrappers with PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r mcp-servers/grok-mcp\requirements.txt
python tests/test_python_installer.py
python -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'
python tests/ci_install_dry_run.py
python tests/private_leak_gate.py .
.\install.ps1 --dry-run --json
```

## Code Style

- Prefer small, explicit Python functions with clear user-facing errors.
- Keep shell and PowerShell wrappers thin; put cross-platform behavior in Python.
- Use temporary `HOME` / `USERPROFILE` and fake CLIs for tests.
- Do not add machine-specific paths, private aliases, credentials, or personal wiki references.
- Preserve the `danger-full-access` warning in README and agent docs.
- Important scripts and configs should keep short `Input / Output / Pos` headers.

## Pull Requests

- Keep each PR focused on one behavior or release task.
- Include the commands you ran and the result.
- Explain any test you intentionally skipped.
- For installer behavior, describe how the change avoids touching a real Claude profile.
- Leave README clone URLs as `https://github.com/<you>/claude-multiengine-router.git` until the release owner replaces the placeholder.

---

# 贡献指南

感谢你帮助这个项目变得更安全、更容易安装。

## 范围

本项目会安装 Claude Code 路由资产、代理 agent 和 Grok MCP server。请保持 macOS、Linux、Windows 三端可用，并确保测试不写入真实用户配置。

## 本地检查

优先运行上方命令；Windows 可用 `python` 和 PowerShell 版本。安装类测试必须使用临时 `HOME` / `USERPROFILE`、fake CLI 或 disposable profile。

## 代码风格

- Python 逻辑保持小函数、清晰错误信息。
- shell / PowerShell 只做薄封装，跨平台逻辑放进 Python。
- 不提交私人路径、私人称呼、凭据或个人知识库引用。
- README 和 agent 文档里的 `danger-full-access` 风险提示必须保留。

## PR 流程

- 一个 PR 解决一个明确问题。
- 写清楚测试命令和结果。
- 如果跳过测试，要说明原因和剩余风险。
- 发布前由维护者录制 Demo GIF、创建真实 GitHub 仓库并替换 README 中的 `<you>` 占位。
