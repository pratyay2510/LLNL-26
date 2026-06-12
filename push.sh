#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository."
  exit 1
fi

git add -A

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  while true; do
    read -r -p "Commit message: " message
    if [[ -n "${message// /}" ]]; then
      break
    fi
    echo "Commit message cannot be empty."
  done
  git commit -m "$message"
fi

git push

echo "Done."
