#!/usr/bin/env bash
# Reusable pinned-lab Scale CSI 16 MiB persistence smoke test.
set -Eeuo pipefail

cd "$(dirname "$0")/.."
KUBECONFIG_PATH=/home/automation/.kube/lab01.conf
EXPECTED_API='https://api.itz-s6fyum.infra01-lb.wdc04.techzone.ibm.com:6443'
PROTECTED_API='https://api.itz-d4xrcs.infra01-lb.wdc04.techzone.ibm.com:6443'
IMAGE='registry.access.redhat.com/ubi9/ubi-minimal:latest'
NS="fusion-scale-io-$(date -u +%Y%m%d%H%M%S)-${RANDOM}"
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
    printf '\nPASS: Scale CSI provision, 16 MiB write, remount, checksum and cleanup.\n'
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

# Use only the new pinned Scale StorageClass; never use Ceph or local disks.
SC='fusionfs1'
sc_json="$(oclab get sc "$SC" -o json)" || fail 'Scale StorageClass fusionfs1 is missing'
[[ "$(jq -r '.provisioner' <<<"$sc_json")" == 'spectrumscale.csi.ibm.com' ]] || fail 'fusionfs1 is not a Scale CSI class'
[[ "$(jq -r '.parameters.volBackendFs' <<<"$sc_json")" == 'lab01-external-scale-fs1' ]] || fail 'Unexpected Scale backend filesystem; expected the verified local mount name'
[[ "$(jq -r '.parameters.clusterId' <<<"$sc_json")" =~ ^[0-9]{12,22}$ ]] || fail 'Unexpected Scale remote cluster ID' 
say "Using verified Scale CSI StorageClass: $SC"
[[ "$(oclab -n ibm-spectrum-scale get filesystem.scale.spectrum.ibm.com lab01-external-scale-fs1 -o json | jq -r 'any(.status.conditions[]?; .type=="Success" and .status=="True")')" == true ]] || fail 'External Scale fs1 is not mounted'

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

say 'Waiting for Scale CSI provisioning and writer pod (up to 5 minutes)...'
if ! oclab wait -n "${NS}" "pod/${WRITER}" --for='jsonpath={.status.phase}=Succeeded' --timeout=300s; then
  oclab get pods,pvc -n "${NS}" -o wide || true
  say 'Relevant PVC and volume events (truncated to avoid session cookies)...'
  oclab get events -n "${NS}" -o json | jq -r '[.items[] | select(.reason == "ProvisioningFailed" or .reason == "FailedMount" or .reason == "FailedAttachVolume") | (.message // "") | split("Set-Cookie:")[0] | .[0:400]] | unique | .[]' || true
  oclab describe pod "${WRITER}" -n "${NS}" | tail -50 || true
  oclab logs "${WRITER}" -n "${NS}" || true
  fail 'Writer pod did not complete; check scheduling, image pull and Scale CSI events'
fi
oclab logs "${WRITER}" -n "${NS}"
[[ "$(oclab get pvc "${PVC}" -n "${NS}" -o jsonpath='{.status.phase}')" == 'Bound' ]] || fail 'Scale PVC is not Bound'

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
say 'Persistent Scale CSI read/write test passed.'
