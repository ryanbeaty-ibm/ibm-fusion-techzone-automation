# 01 — Fresh-cluster deployment runbook

This is the step-by-step procedure to validate the consolidated **v2.1** workflow. The v1.4.2 component scripts previously passed, but the one-command installer has **not** yet been proven on a fresh cluster.

## Before Step 1 — Upload and extract the installer

Complete the **SecureCRT SFTP → Ubuntu SSH** copy/paste steps at the top of the [GitHub README](../README.md#getting-started--transfer-and-install-the-package). The ZIP must be extracted into `~/fusion-lab01-installer` before the `plan` or `deploy` commands below will work.

## Step 1 — Record reservation-specific inputs

| Parameter | What to record | Example ONLY |
|---|---|---|
| `--cluster` | Node name prefix in the reservation | `itz-REPLACE_ME` |
| `--kubeconfig` | Explicit kubeconfig path on Ubuntu | `/home/automation/.kube/lab01.conf` |
| `--scale-host` | Remote Scale management IP or DNS | `10.10.10.202` in the earlier lab |
| `--ceph-disk` | Confirmed blank block device on all 3 infra nodes | `/dev/vde` in the earlier lab |

**Never reuse the previous reservation's cluster ID.** The installer is designed to discover the new remote Scale ID after the connection is established.

## Step 2 — Fresh OpenShift health gate (read-only)

**Do not start Fusion installation merely because all nodes say `Ready`.** A fresh TechZone cluster may initially show the Console Operator unavailable or `kube-apiserver` progressing while the rest of the control plane settles. These are common initialization states; wait for them to clear.

**Ubuntu SSH — Step 2A: inspect the cluster:**

```bash
# Replace lab02.conf with the filename downloaded for THIS reservation.
export KUBECONFIG="$HOME/.kube/lab02.conf"

echo "=== Connected User ==="
oc whoami

echo "=== OpenShift API ==="
oc whoami --show-server

echo "=== Nodes ==="
oc get nodes

echo "=== Cluster Operators ==="
oc get co

echo "=== Console Pods ==="
oc get pods -n openshift-console

echo "=== MachineConfigPools ==="
oc get mcp

echo "=== OpenShift Version ==="
oc get clusterversion
```

**Expected:** `system:admin`, the current reservation's API address, nine `Ready` nodes (3 masters, 3 infrastructure, 3 regular workers), OpenShift 4.21.x, every ClusterOperator `AVAILABLE=True`, `PROGRESSING=False`, `DEGRADED=False`, and all MachineConfigPools `UPDATED=True`, `UPDATING=False`, `DEGRADED=False`, with their ready/updated node counts equal to machine count. ClusterVersion must be `AVAILABLE=True` and `PROGRESSING=False`.

**Ubuntu SSH — Step 2B: only if operators are still settling:**

```bash
oc wait co/kube-apiserver \
  --for=condition=Progressing=False \
  --timeout=10m

oc get co kube-apiserver console
oc get clusterversion
```

This wait command is read-only. Its success proves only that `kube-apiserver` is no longer `Progressing`; **it does not verify the entire cluster**. If an operator remains unavailable, progressing or degraded, investigate or wait before continuing.

**Ubuntu SSH — Step 2C: automated GO/NO-GO validation (requires `jq`):**

```bash
# Fail closed if any part of the brand-new OpenShift cluster is not ready.
oc get nodes -o json | jq -e '
  (.items | length == 9) and
  all(.items[]; any(.status.conditions[]?; .type == "Ready" and .status == "True"))
' >/dev/null &&
oc get co -o json | jq -e '
  all(.items[];
    any(.status.conditions[]?; .type == "Available" and .status == "True") and
    any(.status.conditions[]?; .type == "Progressing" and .status == "False") and
    any(.status.conditions[]?; .type == "Degraded" and .status == "False")
  )
' >/dev/null &&
oc get mcp -o json | jq -e '
  all(.items[];
    .status.machineCount == .status.readyMachineCount and
    .status.machineCount == .status.updatedMachineCount and
    .status.degradedMachineCount == 0 and
    any(.status.conditions[]?; .type == "Updated" and .status == "True") and
    any(.status.conditions[]?; .type == "Updating" and .status == "False") and
    any(.status.conditions[]?; .type == "Degraded" and .status == "False")
  )
' >/dev/null &&
oc get clusterversion version -o json | jq -e '
  (.status.desired.version | startswith("4.21.")) and
  any(.status.conditions[]?; .type == "Available" and .status == "True") and
  any(.status.conditions[]?; .type == "Progressing" and .status == "False")
' >/dev/null &&
echo "PASS: OpenShift is ready for the Fusion installer" ||
{ echo "STOP: OpenShift health check failed; do NOT deploy Fusion yet"; false; }
```

Do not treat the final `STOP` message as a passed prerequisite. Re-run the health checks until the output is `PASS`. **No OpenShift resources are created or modified by Step 2.** Capture the statuses in the [test worksheet](04-TEST-SESSION-TEMPLATE.md). Do not paste kubeconfig, authorization tokens, or raw credentials into GitHub.

## Step 3 — Run read-only plan

```bash
cd "$HOME/fusion-lab01-installer"
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/lab01.conf" \
  --scale-host REPLACE_WITH_REMOTE_SCALE_IP \
  --ceph-disk /dev/vde
```

Expected: validated API and node inventory; a new pinned `work/itz-REPLACE_ME/` directory; a printed list of installation stages. Plan does **not** change cluster resources or check whether the disks are blank.

## Step 4 — Approve storage and reboot operations

Before starting deployment, explicitly check the reservation's **three candidate infra disks are empty**. The playbooks perform additional disk qualification; the person running the command is responsible for confirming these are intended disposable disks. Scale node MachineConfig preparation can reboot the three regular workers.

## Step 5 — Run deployment

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/lab01.conf" \
  --scale-host REPLACE_WITH_REMOTE_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

The installer writes its stage output under `work/<cluster>/logs/install-YYYYMMDDTHHMMSSZ.log` and exits at the first failed stage. **Never blindly delete storage resources or restart the entire installer to recover from a failure.**

## Step 6 — Verify outcomes

Use [02 — Validation](02-VALIDATION.md). A completed run must show successful Ceph and Scale dynamic provisioning, a write, deletion of the writer pod, remount into a reader pod, and a successful SHA-256 checksum check for each storage backend.

## Step 7 — Document the observed result

In the [test worksheet](04-TEST-SESSION-TEMPLATE.md), distinguish **observed** result from **expected** result for every stage. Redact raw HTTP headers, cookies, kubeconfig, credentials and token content. Retain the full private log outside GitHub only as long as needed for troubleshooting.

## Step 8 — Resume only a failed stage

Supported `--from` values: `fusion-ceph`, `ceph-io-test`, `scale-nodeprep`, `scale-operator`, `scale-client`, `scale-external`, `final-verification`.

After diagnosing the failed stage, run the same `deploy` command with the exact same arguments and add `--from scale-operator` (or your failed stage). **Resume does not revalidate all earlier stages.** Confirm previous stages are still healthy before skipping them. The `deploy` action still requires `--claim-disks` and `--allow-worker-reboots` flags when resumed.

## Acceptance criterion

Mark the v2.1 single-command installer as **fresh-lab validated** only when all seven stages report success without manual code patching, and the persisted data checks for both backends pass. If any patch was required, record the version bump and repeat a clean-room test before claiming the new version is proven.

## First-run Scale credentials (v2.1)

The first `deploy` for the new cluster prompts for the Scale GUI username (press Enter for `csi-storage-gui-user`) and its hidden password. The installer encrypts both values using Ansible Vault and saves the encrypted credentials and a separate random key outside the GitHub directory. A later resume on the same Ubuntu host reuses them without prompting. Add `--update-scale-credentials` to a `deploy` command to replace saved credentials when changing reservations. Never commit either credential file or the local key; a user with access to both can decrypt them.
