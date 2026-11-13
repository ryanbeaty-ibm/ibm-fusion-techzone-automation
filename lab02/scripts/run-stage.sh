#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="$ROOT/config/environment.yml"
MODE="${2:-run}"
STAGE="${1:-}"
case "$STAGE" in
  01) PLAY="01-backup-restore-hub.yml" ;;
  02) PLAY="02-noobaa-s3-and-policies.yml" ;;
  03) PLAY="03-filebrowser-backup-restore.yml" ;;
  04) PLAY="04-mongodb-consistent-backup-restore.yml" ;;
  05a) PLAY="05-service-protection-prepare.yml" ;;
  05c) PLAY="05-service-protection-preflight.yml" ;;
  06b) PLAY="06-spoke-agent-bootstrap.yml" ;;
  07) PLAY="07-crosscluster-filebrowser-restore.yml" ;;
  *) echo 'Usage: ./scripts/run-stage.sh {01|02|03|04|05a|05c|06b|07} [syntax|check|run]' >&2; exit 2 ;;
esac
[[ -f "$CONFIG" ]] || { echo 'Missing config/environment.yml: copy the example and edit cluster IDs.' >&2; exit 2; }
ARGS=( -i localhost, -c local "$ROOT/installer/$PLAY" -e "@$CONFIG" )
case "$MODE" in
 syntax) exec ansible-playbook "${ARGS[@]}" --syntax-check ;;
 check) exec ansible-playbook "${ARGS[@]}" --check ;;
 run) exec env ANSIBLE_DISPLAY_OK_HOSTS=false ANSIBLE_DISPLAY_SKIPPED_HOSTS=false ansible-playbook "${ARGS[@]}" ;;
 *) echo 'Mode must be syntax, check, or run' >&2; exit 2 ;;
esac
