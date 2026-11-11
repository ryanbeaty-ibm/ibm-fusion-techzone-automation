# IBM Fusion Lab 01 — TechZone automated deployment

> **Project state:** v1.4.2 installation and storage tests passed on a previous lab. The consolidated **v2.1 single-command installer has not yet passed a full fresh-cluster deployment**. Follow the [fresh-lab runbook](docs/01-FRESH-LAB-RUNBOOK.md) to conduct and record that test.

An independent lab automation project for deploying **IBM Storage Fusion, IBM Fusion Data Foundation / Ceph, and an OpenShift-side IBM Storage Scale data-access client** on a disposable IBM TechZone OpenShift cluster. The lab is expected to provide an **already deployed external IBM Storage Scale server**; this project connects to that server rather than installing a second Scale server.

## Getting started — transfer and install the package

These are the **first two copy-and-paste steps** for the existing Windows + SecureCRT + Ubuntu Ansible-server workflow. First download `IBM-Fusion-Lab01-OneCommand-v2.1.zip` and save it in `D:\Dropbox\Fusion` on the Windows computer.

### Step 1 — SecureCRT SFTP (Windows)

Paste into a **SecureCRT SFTP session** (not the Ubuntu SSH shell):

```text
lcd D:\Dropbox\Fusion
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.1.zip
```

This uploads the ZIP to `/home/automation` on the existing Ubuntu automation server. Change the local path and Ubuntu username/home directory if your environment differs.

### Step 2 — Ubuntu SSH (Ansible server)

Paste into the **Ubuntu SSH session** (not the SFTP prompt):

```bash
mkdir -p ~/fusion-lab01-installer

cd ~/fusion-lab01-installer

unzip -o ~/IBM-Fusion-Lab01-OneCommand-v2.1.zip -d .

ls -lah
```

The extracted project should contain `install-lab01.sh`, `installer/`, `reference/`, and `docs/`. **Extraction does not start the deployment or modify OpenShift.**

> **For public GitHub users:** Once this repository is published, `git clone` is an alternative to SFTP and unzipping a release ZIP. The two steps above document the original SecureCRT workflow, not a mandatory Ansible directory layout.

### Step 3 — Obtain and verify the fresh cluster kubeconfig

Follow [00 — Prerequisites and kubeconfig](docs/00-PREREQUISITES.md). Keep the kubeconfig outside this repository, and verify `oc whoami`, `oc get nodes`, and the actual API endpoint before running the installer.

### Step 4 — Wait for OpenShift to become fully healthy

**Before running `plan` or `deploy`,** perform the copy/paste [fresh-cluster health check](docs/01-FRESH-LAB-RUNBOOK.md#step-2--fresh-openshift-health-gate-read-only). A new TechZone reservation may show all nine nodes `Ready` while OpenShift Operators are still reconciling. Wait until:

- ClusterVersion: `AVAILABLE=True`, `PROGRESSING=False`.
- Every ClusterOperator: `AVAILABLE=True`, `PROGRESSING=False`, `DEGRADED=False`.
- MachineConfigPools: `UPDATED=True`, `UPDATING=False`, `DEGRADED=False` with all configured nodes updated and ready.

An initially unavailable Console Operator or progressing Kubernetes API Server is a **wait-and-recheck condition**, not a reason to start Fusion installation early.

### Step 5 — Plan first, then deploy

Use the [fresh-cluster runbook](docs/01-FRESH-LAB-RUNBOOK.md) to run the read-only `plan`, confirm the blank Ceph disks and remote Scale endpoint, and then explicitly approve disk claims and worker reboots for `deploy`.

## How the installer is structured

```text
install-lab01.sh               # Bash entry point
installer/techzone_lab01.py    # Cluster discovery, generated workspace, stage orchestration
reference/                     # Historic working Ansible playbooks, scripts and templates
work/<cluster>/                # Runtime-generated files and logs (DO NOT COMMIT)
docs/                          # GitHub-facing procedures and validation evidence
```

The shell launcher calls the Python orchestrator. The orchestrator uses `oc` for OpenShift discovery and invokes Ansible playbooks and existing shell tests in order. `reference/` contains historical playbooks with previous lab identifiers; **do not execute them directly on a new cluster**.

## Installer commands (after Steps 1–3)

First, obtain a fresh reservation and a dedicated kubeconfig. See [Prerequisites and access](docs/00-PREREQUISITES.md) before any deployment.

On the Ubuntu automation host, extract the installer, supply the new reservation's values, and generate a read-only plan:

```bash
cd ~/fusion-lab01-installer
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/lab01.conf" \
  --scale-host REPLACE_WITH_REMOTE_SCALE_IP \
  --ceph-disk /dev/vde
```

Only after confirming `/dev/vde` on all three infrastructure nodes is a **blank, disposable disk**, approve deployment and expected worker reboots:

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/lab01.conf" \
  --scale-host REPLACE_WITH_REMOTE_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

These are examples, **not values to paste unchanged**. The installer currently requires OpenShift 4.21.x, exactly nine nodes (`master`, `infra`, `worker`, three each), and `system:admin` on a TechZone API. It must not be used on production or data-bearing clusters.

## What the automation does

| Stage | Work performed |
|---|---|
| `fusion-ceph` | Installs IBM Fusion and Data Foundation/Ceph, qualifies and claims explicitly selected empty local disks |
| `ceph-io-test` | Dynamically provisions Ceph storage; verifies write, pod recreation/remount, and checksum |
| `scale-nodeprep` | Creates a dedicated three-node Scale MachineConfigPool and kernel-devel extension; worker reboots may occur |
| `scale-operator` | Activates the existing IBM Storage Scale Operator |
| `scale-client` | Creates the local three-node data-access client |
| `scale-external` | Connects to the pre-deployed external Scale server, mounts `fs1`, discovers the live remote cluster ID, creates `fusionfs1`, and tests persistence |
| `final-verification` | Checks Fusion/Ceph readiness again |

## Documentation

- [00 — Prerequisites, file transfer and kubeconfig](docs/00-PREREQUISITES.md)
- [01 — New-cluster deployment runbook](docs/01-FRESH-LAB-RUNBOOK.md)
- [02 — Validation and expected outcomes](docs/02-VALIDATION.md)
- [03 — Troubleshooting and resume stages](docs/03-TROUBLESHOOTING.md)
- [04 — Repeatable test-session worksheet](docs/04-TEST-SESSION-TEMPLATE.md)
- [05 — Publishing and security checklist](docs/05-PRE-PUBLISH-CHECKLIST.md)

## Status and scope

On **2026-11-11**, the prior successful installation on `itz-s6fyum` verified a three-OSD Ceph cluster, a three-node Scale client, external Scale connectivity, and 16 MiB persistence tests on both storage backends. That does **not** prove that v2.1 can install into any fresh reservation without modification. The upcoming fresh lab is the release-acceptance test.

This is an independent automation project, **not an official IBM-supported installer**. Product versions, network layout, storage device names, and external Scale details are specific to the TechZone template. IBM training materials remain the property of their owners and are not redistributed here.

**Security:** Never commit kubeconfigs, secrets, passwords, generated workspaces, or raw provisioner logs. v2.1 prompts once for Scale GUI credentials and encrypts them using Ansible Vault outside the project tree. A local user with access to both private Vault data and its key can decrypt the values. See the pre-publish checklist.
