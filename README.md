# Claude Multiengine Router

Claude Code as the controller. Codex and official Grok Build as delegated execution engines.

This project installs a portable local multi-engine agent setup for macOS, Linux, and Windows:

- Claude Code stays responsible for planning, routing, review, and final acceptance.
- Codex handles primary coding, refactoring, debugging, tests, review, and image-generation prompts.
- Official Grok Build handles real-time research, X/web context, and coding fallback or best-of-n comparison.
- Both engines are exposed through Claude proxy agents, and Codex/Grok are also registered as user-scoped MCP servers.

<p style="color:red"><strong>⚠️ Full-permission risk warning: this setup uses Codex with <code>danger-full-access</code>. Codex can access the network and read/write arbitrary local paths. Install only if you understand and accept that risk. Do not delegate destructive operations, secrets, production access, migrations, or unique user data work without explicit confirmation and backups.</strong></p>

## What Gets Installed

```text
~/.claude/
├── skills/agent-router/SKILL.md
├── agents/
│   ├── codex-exec.md
│   ├── codex-fast.md
│   ├── codex-image.md
│   ├── codex-review.md
│   ├── grok-research.md
│   └── grok-coder.md
├── mcp-servers/grok-mcp/
│   ├── server.py
│   ├── test_server.py
│   ├── selftest_stdio.py
│   ├── requirements.txt
│   └── .venv/
└── agent-router/
    ├── config.sh
    └── config.ps1
```

The installer also runs:

```bash
claude mcp add -s user codex -- <codex> mcp-server
claude mcp add -s user grok -- <venv-python> <server.py>
```

On Windows, the same registration is executed through Python argument lists, using the Windows venv interpreter:

```powershell
claude mcp add -s user codex -- <codex> mcp-server
claude mcp add -s user grok -e GROK_BIN=<grok> -e GROK_MODEL=grok-build -- <mcp>\.venv\Scripts\python.exe <mcp>\server.py
```

Existing same-name skills, agents, and Grok MCP files are backed up before replacement unless they were already installed by this project.

## Prerequisites

Phase 2 supports macOS, Linux, and Windows. The install logic lives in `install.py`; `install.sh` and `install.ps1` are thin wrappers.

Install and authenticate these first:

- Claude Code: https://code.claude.com/docs/en/setup
- Codex CLI: https://developers.openai.com/codex/cli
- Grok Build: https://docs.x.ai/build/overview
- Python 3: https://www.python.org/downloads/

Then log in manually:

```bash
codex login
grok login
```

The installer checks `codex login status` and `grok models`. It never logs in for you.

## One-Command Install

macOS/Linux:

```bash
git clone https://github.com/<you>/claude-multiengine-router.git
cd claude-multiengine-router
bash install.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/<you>/claude-multiengine-router.git
cd claude-multiengine-router
.\install.ps1
```

If PowerShell blocks local scripts, allow locally created scripts for the current user, then retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\install.ps1
```

If you do not want to change execution policy, run the Python installer directly:

```powershell
python .\install.py
```

Optional configuration:

```bash
cp config.example.sh config.local.sh
$EDITOR config.local.sh
bash install.sh
```

Configurable values:

- `OUTPUT_DIR`: default `~/.agent-router/output`
- `ENABLE_WIKI_LOG`: default `false`
- `CODEX_MODEL`: default empty, meaning "use Codex config"
- `GROK_MODEL`: default `grok-build`

Advanced env overrides are supported for unusual install paths: `CLAUDE_BIN`, `CODEX_BIN`, `GROK_BIN`, and `PYTHON_BIN`.

Windows PowerShell env override example:

```powershell
$env:OUTPUT_DIR = "$env:USERPROFILE\.agent-router\output"
$env:GROK_MODEL = "grok-build"
.\install.ps1
```

## Usage

Restart Claude Code after installation. Then ask Claude to use the `agent-router` skill when you want multi-engine delegation.

Example prompts:

```text
Use agent-router. Have Codex implement the failing test, then review the diff.
```

```text
Use agent-router. Ask Grok to research current community discussion, then decide whether Codex should implement a patch.
```

Installed proxy agents:

- `codex-exec`: complex coding, refactoring, debugging, tests
- `codex-fast`: small bounded code tasks
- `codex-image`: Codex image-generation prompts and generated assets
- `codex-review`: Codex review of git worktree changes
- `grok-research`: current web/X research through official Grok Build
- `grok-coder`: Grok coding fallback or best-of-n comparison

Installed MCP servers:

- `codex`: runs `codex mcp-server`
- `grok`: Python MCP server exposing `grok_research` and `grok_code`

## Uninstall

```bash
bash uninstall.sh
```

Windows:

```powershell
.\uninstall.ps1
```

The uninstaller backs up same-name installed files under:

```text
~/.claude/backups/claude-multiengine-router-uninstall-<timestamp>/
```

It also removes the user-scoped `codex` and `grok` MCP registrations when the `claude` CLI is available.

## Development Checks

```bash
bash -n install.sh uninstall.sh tests/test_install_temp_home.sh tests/test_uninstall_temp_home.sh
bash tests/test_install_temp_home.sh
bash tests/test_uninstall_temp_home.sh
python3 tests/test_python_installer.py
python3 -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'
```

When PowerShell is available, also run:

```powershell
pwsh -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw .\install.ps1)) | Out-Null; [scriptblock]::Create((Get-Content -Raw .\uninstall.ps1)) | Out-Null"
```

The temp-HOME smoke test uses fake `claude`, `codex`, and `grok` binaries. It does not touch your real `~/.claude`.

## 中文说明

这个项目是一个支持 macOS、Linux、Windows 的本地多引擎路由器：让 Claude Code 做总控，把 Codex 和官方 Grok Build 桥接成 Claude 可调度的 MCP 工具与 proxy 子代理。

核心分工：

- Claude Code：总控、架构、路由、验收。
- Codex：主要写码、重构、调试、测试、审查、生图 prompt。
- 官方 Grok Build：实时调研、X/web 信息、Codex 卡住时的写码备选或 best-of-n 对比。

<p style="color:red"><strong>⚠️ 全权限风险警告：本套配置会让 Codex 使用 <code>danger-full-access</code>。这意味着它可以联网，并读写任意本机路径。安装前必须知情同意；涉及删除、迁移、密钥、生产环境、数据库或唯一数据时，必须先确认范围、备份和回滚方案。</strong></p>

安装前先自己登录：

```bash
codex login
grok login
```

安装：

macOS/Linux：

```bash
bash install.sh
```

Windows PowerShell：

```powershell
.\install.ps1
```

如果 PowerShell 阻止本地脚本，先执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

也可以直接运行 Python 安装器：

```powershell
python .\install.py
```

卸载：

macOS/Linux：

```bash
bash uninstall.sh
```

Windows：

```powershell
.\uninstall.ps1
```

可选配置见 `config.example.sh`。默认输出目录是 `~/.agent-router/output`，wiki 落档提醒默认关闭。
