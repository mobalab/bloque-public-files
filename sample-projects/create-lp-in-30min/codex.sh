#!/usr/bin/env bash

# Shared helper: resolve project root and load .env (if present).
# Intended to be sourced from scripts in bin/.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
project_root="$script_dir"
env_file="$project_root/.env"

if [[ -f "$env_file" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
fi

exec codex "$@"
