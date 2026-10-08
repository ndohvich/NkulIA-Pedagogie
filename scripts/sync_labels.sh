#!/usr/bin/env bash
# Crée (ou met à jour) sur GitHub tous les labels de .github/labels.yml.
# Référencé par labels.yml ; nécessite la CLI `gh` authentifiée (gh auth login).
# Usage : scripts/sync_labels.sh [propriétaire/dépôt]   (défaut : dépôt du dossier courant)
set -euo pipefail

cd "$(dirname "$0")/.."
repo_args=()
[[ $# -ge 1 ]] && repo_args=(--repo "$1")

python3 - "${repo_args[@]}" <<'PY'
import re
import subprocess
import sys

extra = sys.argv[1:]
text = open(".github/labels.yml", encoding="utf-8").read()
count = 0
for block in re.split(r"\n(?=- name:)", text):
    name = re.search(r'^- name:\s*"?([^"\n]+)"?', block, re.M)
    color = re.search(r'color:\s*"?#?([0-9A-Fa-f]{6})"?', block)
    desc = re.search(r'description:\s*"?([^"\n]*)"?', block)
    if not (name and color):
        continue
    subprocess.run(
        ["gh", "label", "create", name.group(1).strip(), "--color", color.group(1),
         "--description", desc.group(1).strip() if desc else "", "--force", *extra],
        check=True,
    )
    count += 1
print(f"{count} labels synchronisés.")
PY
