## Summary / 概述

-

## Test Plan / 测试

- [ ] `bash -n install.sh uninstall.sh tests/test_install_temp_home.sh tests/test_uninstall_temp_home.sh`
- [ ] `python3 tests/test_python_installer.py`
- [ ] `python3 -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'`
- [ ] `python3 tests/ci_install_dry_run.py`
- [ ] `python3 tests/private_leak_gate.py .`

## Safety / 安全

- [ ] Installer tests used temporary `HOME` / `USERPROFILE` or fake CLIs.
- [ ] No real Claude profile, credentials, production data, or destructive local paths were touched.
- [ ] The `danger-full-access` warning remains visible in user-facing docs.
