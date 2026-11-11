#!/usr/bin/env bash
# One command to install/reconcile Fusion Operator and SpectrumFusion on a pinned lab,
# then verify Operator and CR. DOES NOT provision ODF/Ceph or claim disks.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$#" -ne 1 || ! -f "$1" ]]; then
  echo "Usage: bash scripts/deploy-fusion-lab.sh config/local/<target>.yml" >&2
  exit 2
fi
CONFIG="$1"
echo 'IBM Fusion LAB deployment: this invocation accepts IBM Fusion license terms for the chosen target.'
echo "Configuration: $CONFIG"
ansible-playbook -i localhost, --syntax-check playbooks/lab-automate.yml
ansible-playbook -i localhost, --syntax-check playbooks/lab-verify.yml
ansible-playbook -i localhost, -f 1 playbooks/lab-automate.yml \
  -e "@$CONFIG" -e lab_apply=true -e lab_accept_ibm_license=true
ansible-playbook -i localhost, -f 1 playbooks/lab-verify.yml \
  -e "@$CONFIG"
