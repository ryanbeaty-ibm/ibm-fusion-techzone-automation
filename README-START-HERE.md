# Start here — Lab 01 installer

The installer automates Fusion/Ceph installation, Scale client deployment, connection to the TechZone-provided external Scale server, and **both persistent-storage tests**. You do not need to run each playbook manually.

**Current release:** v2.3 cleanup candidate. The preceding v2.2 release passed a fresh-cluster end-to-end test on November 11, 2026. Read the [live validation record](docs/06-LIVE-VALIDATION-2026-11-11.md).

<!-- BEGIN V3.1 INSTALLER-ENTRY -->
## Before Step 1 - Set up your automation environment

**This installer guide assumes you already have an Ubuntu Ansible control node** with Python, Ansible, OpenShift CLI (`oc`), SSH and network access to your TechZone reservation. If you are starting from scratch, follow [Getting started from zero](docs/GETTING-STARTED-FROM-ZERO.md) first. Windows Hyper-V is one example; other compatible Ubuntu hosts work too.

**Download the packaged installer ZIP** from the repository's [Releases page](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases) under the release's **Assets**. If the ZIP is not there yet, the maintainer needs to [publish it](docs/PUBLISH-RELEASE-ARCHIVE.md). Do not mistake GitHub's automatic source-code ZIP for the installer package.

**Version caution:** v2.3 is identified as a cleanup candidate in this repository; v2.2 is the preceding end-to-end validated release. Verify the chosen package's validation status before deployment.
<!-- END V3.1 INSTALLER-ENTRY -->
## 1 — Download a fresh TechZone kubeconfig

On your Windows computer, download the kubeconfig from your current IBM TechZone reservation. Rename it to a descriptive name such as `newlab.conf` and store it temporarily outside any Git repository. Record the new cluster prefix (`itz-...`), the **existing** external Scale server's management address and the disk assigned to Ceph on each infra node.

## 2 — Transfer the kubeconfig using SecureCRT SFTP

The following paths are examples from the tested Windows/Ubuntu setup. Adapt them to your machines.

```text
lcd C:\Users\YOUR_USERNAME\Downloads
cd /home/automation/.kube
put newlab.conf
```

If the remote `.kube` folder does not exist, create it first in your **Ubuntu SSH** session:

```bash
mkdir -p "$HOME/.kube" && chmod 700 "$HOME/.kube"
```

Back in Ubuntu SSH:

```bash
chmod 600 "$HOME/.kube/newlab.conf"
oc --kubeconfig="$HOME/.kube/newlab.conf" whoami
oc --kubeconfig="$HOME/.kube/newlab.conf" whoami --show-server
```

The installer will perform its own node, OpenShift and ClusterOperator checks. You do **not** need to manually perform a long preflight checklist each time.

## 3 — Transfer the release ZIP

Place `IBM-Fusion-Lab01-OneCommand-v2.3.zip` in your Windows working folder and use SecureCRT SFTP:

```text
lcd C:\Users\YOUR_USERNAME\Downloads
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.3.zip
```

In Ubuntu SSH, extract into a **new versioned directory**, not the previously validated v2.2 workspace:

```bash
mkdir -p "$HOME/fusion-lab01-installer-v2.3"
cd "$HOME/fusion-lab01-installer-v2.3"
unzip -o "$HOME/IBM-Fusion-Lab01-OneCommand-v2.3.zip" -d .
```

Alternatively, clone the GitHub repository onto Ubuntu and run the launcher from its root. Do not commit generated `work/` data.

## 4 — Run `plan` (read-only to OpenShift)

```bash
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/newlab.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde
```

Replace **every** placeholder. `plan` pins the target API, checks nine nodes and runs the automatic Ansible cluster health gate. It creates local files, not cluster resources. It does **not** prove the selected disk is empty or that the Scale server is reachable; those are tested during deployment.

## 5 — Deploy the entire lab with one command

**Before running:** confirm the Ceph device on all three infra nodes is intended for destruction. The installer checks disk eligibility immediately before claims and stops on conflicts, but the operator must still supply the correct device name.

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/newlab.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

First deployment: provide Scale GUI credentials when prompted (password input is hidden); they are encrypted with Ansible Vault outside the working tree. No more manual installation steps should be necessary if the target environment matches the tested assumptions.

Look for **`PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.`** At the end, v2.3 also prints per-stage and total elapsed time. Logs reside under `work/<cluster>/logs/` and must not be shared without redaction.

If it stops, see the [troubleshooting guide](docs/03-TROUBLESHOOTING.md). Resume a failed stage with `--from <stage>` only after diagnosing the problem; the runner does not silently disregard errors.

**Scope:** disposable nine-node IBM TechZone OpenShift 4.21.x; not a production installer, not a replacement for the external Scale server, and not the full official course exercise sequence.

## Hyper-V / Ubuntu automation VM prerequisites

For Windows Hyper-V setup and Ubuntu automation dependencies, see [Hyper-V + Ubuntu prerequisites](docs/HYPERV-UBUNTU-PREREQUISITES.md).
