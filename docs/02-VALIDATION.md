# 02 — What counts as a successful installation?

## Known prior result

The previous `itz-s6fyum` lab completed the **v1.4.2** Fusion/Ceph/Scale installation and the final Scale 16 MiB write/remount/SHA-256 test on 2026-11-11. It used a pre-deployed external Scale server, not a new Scale storage server installed by Ansible.

## Read-only verification commands on a new lab

```bash
export KUBECONFIG="$HOME/.kube/lab01.conf"

echo '=== Nodes ==='
oc get nodes

echo '=== Fusion ==='
oc get csv -n ibm-spectrum-fusion-ns | grep isf-operator
oc get pods -n ibm-spectrum-fusion-ns

echo '=== Ceph / Data Foundation ==='
oc get storageclusters.ocs.openshift.io -n openshift-storage
oc get pods -n openshift-storage | grep -E 'rook-ceph-osd|rook-ceph-operator'

echo '=== Dedicated Scale workers ==='
oc get mcp scale
oc get pods -n ibm-spectrum-scale -l app.kubernetes.io/name=core -o wide

echo '=== Remote Scale objects ==='
oc get remoteclusters.scale.spectrum.ibm.com -n ibm-spectrum-scale
oc get filesystems.scale.spectrum.ibm.com -n ibm-spectrum-scale

echo '=== Scale StorageClass ==='
oc get storageclass fusionfs1 -o yaml
```

**Expected:** Fusion running, Ceph healthy, three worker Scale core pods ready, remote Scale connection and local filesystem configured, and a `fusionfs1` StorageClass using the **local mounted filesystem resource name** in `volBackendFs`.

## Dynamic storage validation

The installer runs its own isolated checks, creating and deleting a temporary namespace for each backend. Evidence to capture from a clean deployment log:

- Ceph CSI: PVC provisioned, writer wrote 16 MiB, reader remounted and verified the SHA-256 checksum, temporary namespace removed.
- Scale CSI: PVC provisioned, writer wrote 16 MiB, reader remounted and verified the SHA-256 checksum, temporary namespace removed.
- Final verification reported success; the installer printed `PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.`

The local mounted Scale filesystem name follows the generated pattern `<cluster>-external-scale-fs1` in v2.1. The dynamic remote cluster ID must be discovered live; do not append it to the filesystem name for `volBackendFs`.

## Lab versus full IBM course

This automates the **installation and storage-validation subset** of IBM's Installation and Configuration lab. It does not claim completion of additional manual course exercises, quizzes, backup/restore tasks, or other separate learning plans.
