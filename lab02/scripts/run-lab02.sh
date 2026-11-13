#!/usr/bin/env bash
# One entry point for the full Lab 02. Manual Fusion GUI operations are explicit pauses.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STEPS=(01 02 03 04 05a 05b 05c 06a 06b 07)
FROM=01
usage() {
  cat <<'EOF'
Usage: bash scripts/run-lab02.sh [--plan] [--from 01|02|03|04|05a|05b|05c|06a|06b|07]

Single guided run: 01-04 automated; 05a automated; 05b Fusion GUI pause;
05c automated preflight; 06a Fusion GUI pause; 06b automated spoke install;
07 automated cross-cluster restore + SHA-256 verification.

Use --from <stage> to resume after a stopped or previously completed stage.
EOF
}
if [[ "${1:-}" == '--plan' ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == '--from' && $# -eq 2 ]]; then
  FROM="$2"
elif [[ $# -ne 0 ]]; then
  usage >&2; exit 2
fi
FOUND=false
for s in "${STEPS[@]}"; do [[ "$s" == "$FROM" ]] && FOUND=true; done
[[ "$FOUND" == true ]] || { echo "Unknown resume stage: $FROM" >&2; usage >&2; exit 2; }
[[ -f "$ROOT/config/environment.yml" ]] || {
  echo 'Missing lab02/config/environment.yml. Copy and edit config/environment.example.yml first.' >&2; exit 2;
}
for cmd in ansible-playbook oc python3 openssl curl; do
  command -v "$cmd" >/dev/null || { echo "Missing prerequisite: $cmd" >&2; exit 2; }
done
run() {
  local stage="$1"
  printf '\n===== LAB 02 | AUTOMATED STAGE %s =====\n' "$stage"
  bash bash "$ROOT/scripts/run-stage.sh" "$stage" run
}
checkpoint() {
  local stage="$1"
  local message="$2"
  printf '\n===== LAB 02 | MANUAL FUSION UI CHECKPOINT %s =====\n' "$stage"
  printf '%s\n' "$message"
  printf '\nDocumentation: %s\n\n' "$ROOT/docs/manual-checkpoints.md"
  local reply=''
  read -r -p 'After verifying the UI step, type CONTINUE (or Ctrl+C to stop): ' reply
  if [[ "$reply" != 'CONTINUE' ]]; then
    echo "Stopped safely at stage $stage. Resume: bash scripts/run-lab02.sh --from $stage" >&2
    exit 3
  fi
}
STARTED=false
for stage in "${STEPS[@]}"; do
  [[ "$stage" == "$FROM" ]] && STARTED=true
  [[ "$STARTED" == true ]] || continue
  case "$stage" in
    01|02|03|04|05a|05c|06b|07) run "$stage" ;;
    05b)
      checkpoint 05b 'In HUB Fusion Backup & restore > Service protection: configure the dedicated S3 location using the bucket/endpoint shown in 05a, use OBC Secret credentials and the hub certificate Secret. Create a daily backup policy, initiate a backup now, and VERIFY that the first service backup is Completed in the UI. This cannot currently be completed by our supported Ansible workflow.'
      ;;
    06a)
      checkpoint 06a 'In HUB Fusion Backup & restore > Topology > Connect cluster: generate the spoke-agent deployment YAML with the spoke StorageClass. Download and copy BackupAndRestoreAgentDeployment.yaml to your Ubuntu HOME directory with chmod 600. It contains a 1-hour token: do not commit it. If the spoke is already Connected/Healthy, no fresh YAML is required.'
      ;;
  esac
done
printf '\n===== LAB 02 COMPLETE =====\n'
printf 'All automated steps returned successfully. Confirm Service Protection Completed and Topology Connected/Healthy in Fusion hub GUI.\n'
