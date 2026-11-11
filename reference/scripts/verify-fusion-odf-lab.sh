#!/usr/bin/env bash
# Read-only status verification; does not need --claim-disks.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$#" -ne 2 || ! -f "$1" || ! -f "$2" ]]; then
  echo 'Usage: bash scripts/verify-fusion-odf-lab.sh config/local/techzone-2.yml config/local/odf-lab-2.yml' >&2
  exit 2
fi
ansible-playbook -i localhost, -f 1 playbooks/lab-verify.yml -e "@$1"
ansible-playbook -i localhost, -f 1 playbooks/lab-odf-verify.yml -e "@$1" -e "@$2"
echo 'PASS: Fusion, Data Foundation and Ceph readiness verified (read only).'
