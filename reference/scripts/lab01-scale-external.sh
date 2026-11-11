#!/usr/bin/env bash
# IBM Fusion Lab 01 v2.1: attach pre-existing Storage Scale system to proven local client.
# No worker config, Ceph modifications, or remote storage server installation.
set -Eeuo pipefail
cd "$(dirname "$0")/.."
[[ "${1:-}" == deploy && $# -eq 1 ]] || { echo 'Usage: bash scripts/lab01-scale-external.sh deploy' >&2; exit 2; }
KCFG=/home/automation/.kube/lab01.conf
CONFIG=config/local/lab01-scale-external.yml
EXPECTED_API='https://api.itz-s6fyum.infra01-lb.wdc04.techzone.ibm.com:6443'
for t in oc ansible-playbook jq awk; do command -v "$t" >/dev/null || { echo "Missing $t" >&2; exit 2; }; done
for f in "$KCFG" "$CONFIG" playbooks/lab01-scale-render-remote.yml playbooks/lab01-scale-connect-remote.yml playbooks/lab01-scale-mount-filesystem.yml playbooks/lab01-scale-create-storageclass.yml; do
 [[ -r "$f" ]] || { echo "Missing $f" >&2; exit 2; }
done
oclab() { oc --kubeconfig="$KCFG" "$@"; }
[[ "$(oclab whoami --show-server)" == "$EXPECTED_API" ]] || { echo 'Wrong cluster; refusing Lab 01 external mount' >&2; exit 1; }
[[ "$(oclab whoami)" == 'system:admin' ]] || { echo 'Missing cluster admin' >&2; exit 1; }
[[ "$(oclab get mcp scale -o jsonpath='{.status.readyMachineCount}')" == 3 ]] || { echo 'Scale MCP not 3/3 ready' >&2; exit 1; }
[[ "$(oclab -n ibm-spectrum-scale get deploy ibm-spectrum-scale-controller-manager -o jsonpath='{.status.readyReplicas}')" == 1 ]] || { echo 'Scale operator not ready' >&2; exit 1; }
# Check the local cluster and three core pods BEFORE connecting external storage.
[[ "$(oclab -n ibm-spectrum-scale get clusters.scale.spectrum.ibm.com ibm-spectrum-scale -o json | jq -r 'any(.status.conditions[]?; .type=="Success" and .status=="True")')" == true ]] || { echo 'Local Scale client Cluster not configured' >&2; exit 1; }
cores="$(oclab -n ibm-spectrum-scale get pods -l app.kubernetes.io/name=core -o json)"
[[ "$(jq -r '.items|length' <<<"$cores")" == 3 ]] || { echo 'Not exactly 3 Scale core pods' >&2; exit 1; }
[[ "$(jq -r '[.items[] | select(any(.status.conditions[]?; .type=="Ready" and .status=="True"))]|length' <<<"$cores")" == 3 ]] || { echo 'Scale cores not all Ready' >&2; exit 1; }
[[ "$(jq -r '.items[].spec.nodeName' <<<"$cores" | sort)" == "$(printf '%s\n' itz-s6fyum-worker-{1..3} | sort)" ]] || { echo 'Scale core pods on wrong workers' >&2; exit 1; }
oclab -n openshift-storage get storagecluster ocs-storagecluster >/dev/null || { echo 'Ceph is missing' >&2; exit 1; }
mkdir -p logs
LOG="logs/lab01-scale-external-$(date -u +%Y%m%dT%H%M%SZ).log"
echo "PASS: pinned Lab 01, Scale core 3/3, operator ready, Ceph present. Log: $PWD/$LOG" | tee -a "$LOG"
echo 'This attaches only the existing TechZone external Scale server 10.10.10.202 and fs1.'
echo 'Using per-cluster encrypted Scale GUI credentials from Ansible Vault.'
run() { echo "=== $1 ===" | tee -a "$LOG"; shift; "$@" 2>&1 | tee -a "$LOG"; }
# Vault paths point to owner-only files outside this project; only the GUI connection
# step needs decryption. No password is put in argv, shell history or process env.
[[ -r "${FUSION_SCALE_VAULT_VARS_FILE:-}" && -r "${FUSION_SCALE_VAULT_PASSWORD_FILE:-}" ]] || {
  echo 'Scale Vault credentials unavailable. Run the top-level install-lab01.sh command.' >&2
  exit 2
}
ans() {
  local playbook="$1"
  shift
  local args=(ansible-playbook -i localhost, "$playbook" -e "@$CONFIG" -e scale_apply_enabled=true)
  if [[ "$playbook" == 'playbooks/lab01-scale-connect-remote.yml' ]]; then
    args+=(--vault-password-file "$FUSION_SCALE_VAULT_PASSWORD_FILE" -e "@$FUSION_SCALE_VAULT_VARS_FILE")
  fi
  "${args[@]}" "$@"
}
run 'Render remote Scale connection and fs1 manifests' ans playbooks/lab01-scale-render-remote.yml
run 'Connect pre-deployed Scale server (encrypted Vault credentials)' ans playbooks/lab01-scale-connect-remote.yml
run 'Mount pre-deployed remote filesystem fs1' ans playbooks/lab01-scale-mount-filesystem.yml
CORE="$(jq -r '.items[0].metadata.name' <<<"$cores")"
echo '=== Discover live remote cluster ID from successful local Scale client connection ===' | tee -a "$LOG"
REMOTE="$(oclab -n ibm-spectrum-scale exec "$CORE" -c gpfs -- mmremotecluster show all)" || { echo 'Cannot query remote Scale cluster ID; send the last error (do not guess ID)' >&2; exit 1; }
# Print only the cluster identity lines, not credentials or SHA data.
printf '%s\n' "$REMOTE" | grep -Ei '^Cluster (name|id):' | tee -a "$LOG" || true
mapfile -t IDS < <(printf '%s\n' "$REMOTE" | awk -F: 'tolower($1) ~ /^cluster id[[:space:]]*$/ {gsub(/[[:space:]]/,"",$2); print $2}')
[[ "${#IDS[@]}" == 1 && "${IDS[0]}" =~ ^[0-9]{12,22}$ ]] || { echo 'Cannot uniquely identify the remote Scale cluster ID; stopping before StorageClass creation. Share mmremotecluster output without SHA digests.' >&2; exit 1; }
ID="${IDS[0]}"
run 'Create verified Fusion Scale StorageClass (no Ceph changes)' ans playbooks/lab01-scale-create-storageclass.yml -e "scale_cluster_id=$ID"
run 'Prove Scale CSI provisioning, write, remount, and checksum' bash scripts/lab01-scale-io-test.sh
printf '\nPASS: LAB 01 external IBM Scale fs1, StorageClass fusionfs1, and persistence test completed.\n' | tee -a "$LOG"
