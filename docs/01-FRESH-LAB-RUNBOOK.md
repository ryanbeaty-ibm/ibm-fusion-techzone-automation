# 01 — Fresh-cluster deployment runbook

This is the step-by-step procedure to validate the consolidated **v2.3** workflow. The v2.2 one-command release passed all stages on a fresh cluster. v2.3 is a cleanup candidate that still needs separate clean-room validation.

## Step 1 — Record reservation-specific inputs

| Parameter | What to record | Example ONLY |
|---|---|---|
| `--cluster` | Node name prefix in the reservation | `itz-REPLACE_ME` |
| `--kubeconfig` | Explicit kubeconfig path on Ubuntu | `/home/automation/.kube/lab01.conf` |
| `--scale-host` | Remote Scale management IP or DNS | `10.10.10.202` in the earlier lab |
| `--ceph-disk` | Confirmed blank block device on all 3 infra nodes | `/dev/vde` in the earlier lab |

**Never reuse the previous reservation's cluster ID.** The installer is designed to discover the new remote Scale ID after the connection is established.

## Step 2 — Optional manual snapshot (the installer now runs these health checks automatically)

```bash
export KUBECONFIG="$HOME/.kube/lab01.conf"
oc whoami
oc whoami --show-server
oc get nodes
oc get clusterversion
oc get mcp
oc get storageclass
oc get csv -A
```

Record the results in [test-session worksheet](04-TEST-SESSION-TEMPLATE.md). Don't paste kubeconfig contents or raw bearer tokens into documentation.

## Step 3 — Run read-only plan

```bash
cd "$HOME/fusion-lab01-installer"
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/lab01.conf" \
  --scale-host REPLACE_WITH_REMOTE_SCALE_IP \
  --ceph-disk /dev/vde
```

Expected: validated API and nine Ready nodes; a new pinned `work/itz-REPLACE_ME/`
directory; **automatic Ansible checks of ClusterVersion, every ClusterOperator,
and every MachineConfigPool**; a printed list of stages. If any cluster operator
is Progressing or Degraded, or any MachineConfigPool is not fully Updated, the
installer stops before installation. Plan does **not** change cluster resources,
prove external Scale reachability, or check whether the disks are blank. Those
checks are performed in the relevant deployment phases.

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

Mark the v2.3 single-command installer as **fresh-lab validated** only when all seven stages report success without manual code patching, and the persisted data checks for both backends pass. If any patch was required, record the version bump and repeat a clean-room test before claiming the new version is proven.

## First-run Scale credentials (v2.3)

The first `deploy` for the new cluster prompts for the Scale GUI username (press Enter for `csi-storage-gui-user`) and its hidden password. The installer encrypts both values using Ansible Vault and saves the encrypted credentials and a separate random key outside the GitHub directory. A later resume on the same Ubuntu host reuses them without prompting. Add `--update-scale-credentials` to a `deploy` command to replace saved credentials when changing reservations. Never commit either credential file or the local key; a user with access to both can decrypt them.
