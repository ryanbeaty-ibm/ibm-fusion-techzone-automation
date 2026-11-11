#!/usr/bin/env bash
# Reusable pinned-lab Ceph RBD 16 MiB persistence smoke test.
set -Eeuo pipefail

cd "$(dirname "$0")/.."
CONFIG="${1:-config/local/techzone-2.yml}"
[[ "$#" -le 1 && -f "$CONFIG" ]] || { echo 'Usage: bash scripts/test-fusion-ceph-io-lab.sh [config/local/techzone-2.yml]' >&2; exit 2; }
# Read exactly the target configured for this lab; do not fall back to global kubeconfig.
CONFIG_VALUES="$(python3 - "$CONFIG" <<'PYCONFIG'
import sys, yaml
x=yaml.safe_load(open(sys.argv[1]))
for key in ('kubeconfig_path','expected_api_server','protected_api_server'):
    value=x.get(key)
    if not isinstance(value,str) or not value:
        sys.exit(f'Missing required {key} in {sys.argv[1]}')
    print(value)
PYCONFIG
)" || { echo 'Cannot parse pinned target config' >&2; exit 2; }
mapfile -t CONFIG_SETTINGS <<< "$CONFIG_VALUES"
KUBECONFIG_PATH="${CONFIG_SETTINGS[0]}"
EXPECTED_API="${CONFIG_SETTINGS[1]}"
PROTECTED_API="${CONFIG_SETTINGS[2]}"
IMAGE='registry.access.redhat.com/ubi9/ubi-minimal:latest'
NS="fusion-ceph-io-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
PVC='fusion-io-test'
WRITER='fusion-io-writer'
READER='fusion-io-reader'
created=0

say() { printf '\n[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

oclab() { oc "--kubeconfig=${KUBECONFIG_PATH}" "$@"; }

cleanup() {
  local result=$?
  trap - EXIT
  if (( created )); then
    say "Cleaning up namespace ${NS} (test pods and PVC only)..."
    if ! oclab delete namespace "${NS}" --wait=true --timeout=180s; then
      printf 'WARNING: Cleanup did not finish. Inspect namespace %s on the configured lab.\n' "${NS}" >&2
      result=1
    fi
  fi
  if (( result == 0 )); then
    printf '\nPASS: Ceph RBD provision, 16 MiB write, remount, checksum and cleanup.\n'
  else
    printf '\nFAIL: Storage I/O test incomplete; check output above.\n' >&2
  fi
  exit "${result}"
}
trap cleanup EXIT

[[ -f "${KUBECONFIG_PATH}" ]] || fail "the configured lab kubeconfig not found: ${KUBECONFIG_PATH}"
command -v oc >/dev/null || fail 'OpenShift oc CLI not found'
command -v jq >/dev/null || fail 'jq not found'
actual_api="$(oclab whoami --show-server)" || fail 'Cannot resolve the current OpenShift API'
[[ "${actual_api}" != "${PROTECTED_API}" && "${actual_api}" == "${EXPECTED_API}" ]] ||
  fail "REFUSING wrong cluster. Actual=${actual_api}; expected the configured lab=${EXPECTED_API}"
say "Confirmed the configured lab API: ${actual_api}"

# Only choose a known RBD class. Do not pick the 3 physical LocalVolume backing PVs.
sc_json="$(oclab get storageclass -o json)" || fail 'Cannot list StorageClasses'
mapfile -t rbd_classes < <(jq -r '.items[] | select(.provisioner == "openshift-storage.rbd.csi.ceph.com") | .metadata.name' <<<"${sc_json}")
if ((${#rbd_classes[@]} == 0)); then
  fail 'No Ceph RBD StorageClass found; storage setup may be incomplete'
elif ((${#rbd_classes[@]} == 1)); then
  SC="${rbd_classes[0]}"
elif printf '%s\n' "${rbd_classes[@]}" | grep -Fxq 'ocs-storagecluster-ceph-rbd'; then
  SC='ocs-storagecluster-ceph-rbd'
else
  fail "Multiple RBD classes found; refusing ambiguous selection: ${rbd_classes[*]}"
fi
say "Using Ceph RBD StorageClass: ${SC}"

phase="$(oclab get storagecluster ocs-storagecluster -n openshift-storage -o jsonpath='{.status.phase}')" ||
  fail 'Expected the configured lab StorageCluster does not exist'
[[ "${phase}" == 'Ready' ]] || fail "Ceph StorageCluster is ${phase:-unknown}, not Ready"

# Namespace is unique to this run; never adopt or clean up someone else's namespace.
oclab create namespace "${NS}" >/dev/null || fail "Could not create isolated namespace ${NS}"
created=1
say "Created temporary namespace: ${NS}"

cat <<YAML | oclab apply -n "${NS}" -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${PVC}
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ${SC}
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: ${WRITER}
spec:
  restartPolicy: Never
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: writer
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
      image: ${IMAGE}
      imagePullPolicy: IfNotPresent
      command: ["/bin/sh", "-ec"]
      args:
        - |
          dd if=/dev/urandom of=/data/fusion-test.bin bs=1M count=16 status=none
          sha256sum /data/fusion-test.bin > /data/fusion-test.sha256
          sync
          echo "WRITE_OK: 16 MiB written and checksum recorded"
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: ${PVC}
YAML

say 'Waiting for RBD provisioning and writer pod (up to 5 minutes)...'
if ! oclab wait -n "${NS}" "pod/${WRITER}" --for='jsonpath={.status.phase}=Succeeded' --timeout=300s; then
  oclab get pods,pvc -n "${NS}" -o wide || true
  oclab describe pod "${WRITER}" -n "${NS}" | tail -50 || true
  oclab logs "${WRITER}" -n "${NS}" || true
  fail 'Writer pod did not complete; check scheduling, image pull and RBD CSI events'
fi
oclab logs "${WRITER}" -n "${NS}"
[[ "$(oclab get pvc "${PVC}" -n "${NS}" -o jsonpath='{.status.phase}')" == 'Bound' ]] || fail 'RBD PVC is not Bound'

say 'Deleting writer pod to prove data persists after unmount...'
oclab delete pod "${WRITER}" -n "${NS}" --wait=true --timeout=120s >/dev/null

cat <<YAML | oclab apply -n "${NS}" -f -
apiVersion: v1
kind: Pod
metadata:
  name: ${READER}
spec:
  restartPolicy: Never
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: reader
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
      image: ${IMAGE}
      imagePullPolicy: IfNotPresent
      command: ["/bin/sh", "-ec"]
      args:
        - |
          sha256sum -c /data/fusion-test.sha256
          test "\$(wc -c < /data/fusion-test.bin)" -eq 16777216
          echo "READ_OK: 16 MiB persisted and SHA-256 verified after pod recreation"
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: ${PVC}
YAML

say 'Waiting for reader pod to remount and verify checksum (up to 5 minutes)...'
if ! oclab wait -n "${NS}" "pod/${READER}" --for='jsonpath={.status.phase}=Succeeded' --timeout=300s; then
  oclab get pods,pvc -n "${NS}" -o wide || true
  oclab describe pod "${READER}" -n "${NS}" | tail -50 || true
  oclab logs "${READER}" -n "${NS}" || true
  fail 'Reader pod could not verify persisted data'
fi
oclab logs "${READER}" -n "${NS}"
say 'Persistent Ceph RBD read/write test passed.'
