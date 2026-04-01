#!/usr/bin/env bash
# FreedomForge AI — launcher
cd "$(dirname "${BASH_SOURCE[0]}")"
source "$(dirname "${BASH_SOURCE[0]}")/.venv/bin/activate"
exec python "$(dirname "${BASH_SOURCE[0]}")/main.py" "$@"
