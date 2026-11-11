#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$#" -ne 2 ]]; then
  echo "Usage: bash scripts/audit-fusion-storage-lab.sh config/local/techzone-2.yml config/local/odf-lab-2.yml" >&2
  exit 2
fi
CONFIG="$1"
DISKS="$2"
[[ -f "$CONFIG" && -f "$DISKS" ]] || { echo 'Missing input configuration' >&2; exit 2; }
ansible-playbook -i localhost, --syntax-check playbooks/lab-storage-audit.yml
ansible-playbook -i localhost, -f 1 playbooks/lab-storage-audit.yml -e "@$CONFIG" -e "@$DISKS"
