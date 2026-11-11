#!/usr/bin/env bash
# Install/reconcile Fusion and IBM Data Foundation, then provision exactly 3 reviewed Ceph disks.
# Explicit one-run --claim-disks acknowledgement is mandatory for local PV/StorageCluster.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$#" -ne 3 || "$3" != "--claim-disks" || ! -f "$1" || ! -f "$2" ]]; then
  echo 'Usage: bash scripts/deploy-fusion-odf-lab.sh config/local/<target>.yml config/local/<storage>.yml --claim-disks' >&2
  echo 'WARNING: --claim-disks authorizes ODF to consume the three explicitly selected local devices.' >&2
  exit 2
fi
TARGET="$1"
DISKS="$2"
# All components ship together in v1.0; verify repository integrity.
for f in scripts/deploy-fusion-lab.sh scripts/audit-fusion-storage-lab.sh \
         playbooks/lab-odf-service.yml playbooks/lab-odf-storage.yml playbooks/lab-odf-verify.yml; do
  [[ -f "$f" ]] || { echo "Missing $f; re-extract the full v1.0 package." >&2; exit 2; }
done
printf 'LAB target: %s | reviewed disks: %s\n' "$TARGET" "$DISKS"
for y in playbooks/lab-odf-service.yml playbooks/lab-odf-storage.yml playbooks/lab-odf-verify.yml; do
  ansible-playbook -i localhost, --syntax-check "$y"
done
# v0.7 verifies Fusion's exact pinned cluster and idempotently initializes the CR.
bash scripts/deploy-fusion-lab.sh "$TARGET"
# Pin the target again before deciding whether to audit blank media.
TARGET_API=$(python3 -c 'import sys,yaml;print(yaml.safe_load(open(sys.argv[1]))["expected_api_server"])' "$TARGET")
ACTUAL_API=$(oc --kubeconfig="$(python3 -c 'import sys,yaml;print(yaml.safe_load(open(sys.argv[1]))["kubeconfig_path"])' "$TARGET")" whoami --show-server)
[[ "$TARGET_API" == "$ACTUAL_API" ]] || { echo 'STOP: cluster API differs from target config.' >&2; exit 1; }
# Only re-audit BLANK media before any storage claim exists.
# A previous interrupted run may have created a LocalVolume and PVs but not yet
# created a StorageCluster. Never re-run the blank-media audit on those disks.
KCONF=$(python3 -c 'import sys,yaml;print(yaml.safe_load(open(sys.argv[1]))["kubeconfig_path"])' "$TARGET")
LV_NAME=$(python3 -c 'import sys,yaml;print(yaml.safe_load(open(sys.argv[1])).get("odf_local_volume_name", "fusion-ceph-local"))' "$DISKS")
EXISTING_SC=''
EXISTING_LV=''
if [[ -n "$(oc --kubeconfig="$KCONF" get crd storageclusters.ocs.openshift.io -o name --ignore-not-found)" ]]; then
  EXISTING_SC=$(oc --kubeconfig="$KCONF" get storagecluster ocs-storagecluster -n openshift-storage -o name --ignore-not-found)
fi
if [[ -n "$(oc --kubeconfig="$KCONF" get crd localvolumes.local.storage.openshift.io -o name --ignore-not-found)" ]]; then
  EXISTING_LV=$(oc --kubeconfig="$KCONF" get localvolume "$LV_NAME" -n openshift-local-storage -o name --ignore-not-found)
fi
if [[ -z "$EXISTING_SC" && -z "$EXISTING_LV" ]]; then
  bash scripts/audit-fusion-storage-lab.sh "$TARGET" "$DISKS"
else
  echo "Existing storage claim resource(s): StorageCluster=${EXISTING_SC:-none} LocalVolume=${EXISTING_LV:-none}"
  echo 'Skipping blank-disk audit; downstream playbooks validate existing storage without recreating claims.'
fi
ansible-playbook -i localhost, -f 1 playbooks/lab-odf-service.yml \
  -e "@$TARGET" -e "@$DISKS" -e odf_apply=true
ansible-playbook -i localhost, -f 1 playbooks/lab-odf-storage.yml \
  -e "@$TARGET" -e "@$DISKS" -e approve_disk_claim=true
ansible-playbook -i localhost, -f 1 playbooks/lab-odf-verify.yml \
  -e "@$TARGET" -e "@$DISKS"
echo 'PASS: Fusion + Data Foundation + local Ceph storage verified.'
