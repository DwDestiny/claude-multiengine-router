# MCP Servers Folder Guide

## Boundary

This folder contains MCP server implementations bundled by the installer.

## Rules

- MCP servers must resolve local binaries through env vars first, then `PATH`, then a clear install/login error.
- Do not assume a specific username, home directory, or machine layout.
- Keep dependencies listed in each server's `requirements.txt`.
