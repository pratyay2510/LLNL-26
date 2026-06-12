#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository."
  exit 1
fi

git pull --rebase

echo "Done."
