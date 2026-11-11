# 00 — Prerequisites, SFTP and kubeconfig

## Requirements: verified vs. assumed

The **v2.1 code** checks all these details before executing its stages:

- IBM TechZone OpenShift Container Platform (OCP) **4.21.x** environment, with exactly **3 masters, 3 infrastructure workers, and 3 regular workers**.
- Cluster node names follow the `itz-XXXXXX-{master,infra,worker}-{1,2,3}` convention; all must be Ready.
- A functioning `oc` client and an explicit, named kubeconfig whose identity is `system:admin`.
- Existing, **pre-deployed external IBM Storage Scale server** accessible from the cluster, with filesystem `fs1`.
- A reviewed, blank nonrotational storage disk on each infrastructure node; the known example was `/dev/vde` and the installer requires at least 400 GB per disk.
- An Ubuntu automation host with `bash`, `unzip`, `oc`, `ansible-playbook`, `ansible-vault`, `jq`, `python3` with the PyYAML package, and standard Linux utilities.

The program does **not** install these dependencies for you, test external Scale network connectivity during `plan`, or confirm that a candidate disk is empty during `plan`. Disk qualification occurs in the deployment stages.

## First — Transfer and extract the installer

The following commands are for the established Windows + SecureCRT SFTP + Ubuntu SSH workflow. **They install the files; they do not deploy OpenShift resources.** Download `IBM-Fusion-Lab01-OneCommand-v2.1.zip` to `D:\Dropbox\Fusion` before starting.

**Step 1 — SecureCRT SFTP (Windows)**

```text
lcd D:\Dropbox\Fusion
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.1.zip
```

**Step 2 — Ubuntu SSH (Ansible server)**

```bash
mkdir -p ~/fusion-lab01-installer

cd ~/fusion-lab01-installer

unzip -o ~/IBM-Fusion-Lab01-OneCommand-v2.1.zip -d .

ls -lah
```

Now obtain the new TechZone reservation and kubeconfig as described below. These commands assume the remote Ubuntu account is `automation` and the Windows folder is `D:\Dropbox\Fusion`; adjust when necessary. Public GitHub users may clone the repository instead of using SFTP.

## 1. Obtain a TechZone reservation

Record the reservation's **cluster prefix, OpenShift API endpoint, kubeconfig download location, external Scale management IP/hostname, external filesystem name, and candidate Ceph disk path**. Do not infer that `10.10.10.202` or `/dev/vde` is correct for every reservation.

## 2. Transfer the kubeconfig to Ubuntu

Example when using SecureCRT SFTP on a Windows PC with the working Dropbox folder `D:\Dropbox\Fusion`:

```text
lcd D:\Dropbox\Fusion
cd /home/automation/.kube
put lab01.conf
```

If `.kube` does not yet exist, create it first **in an Ubuntu SSH shell**, not in the SFTP command prompt:

```bash
mkdir -p "$HOME/.kube"
chmod 700 "$HOME/.kube"
```

The file is named `lab01.conf` here for convenience; keep the credentials outside the git repository. On Ubuntu:

```bash
chmod 600 "$HOME/.kube/lab01.conf"
export KUBECONFIG="$HOME/.kube/lab01.conf"
oc whoami
oc whoami --show-server
oc get nodes
oc get clusterversion
```

Expected: `system:admin`, the **new** reservation API, nine Ready nodes, and OpenShift 4.21.x. If `oc` is missing, install the appropriate Red Hat OpenShift CLI for the automation host before continuing.

## 2a. Wait for fresh OpenShift cluster health (read-only)

A new reservation can report all nine nodes `Ready` **before** its cluster operators finish installation and reconciliation. Use these copy/paste-ready Ubuntu SSH commands after transferring the kubeconfig (replace the filename if you used a different name):

```bash
export KUBECONFIG="$HOME/.kube/lab02.conf"

echo "=== Cluster Operators ==="
oc get co

echo "=== Console Pods ==="
oc get pods -n openshift-console

echo "=== MachineConfigPools ==="
oc get mcp

echo "=== OpenShift Version ==="
oc get clusterversion
```

If an operator is still initializing, **do not run the installer**. For example, when `kube-apiserver` is progressing or Console is temporarily unavailable, wait and recheck:

```bash
oc wait co/kube-apiserver \
  --for=condition=Progressing=False \
  --timeout=10m

oc get co kube-apiserver console
oc get clusterversion
```

**Go/no-go:** Every ClusterOperator must be `AVAILABLE=True`, `PROGRESSING=False`, `DEGRADED=False`. ClusterVersion must be `AVAILABLE=True`, `PROGRESSING=False`, and MachineConfigPools must show `UPDATED=True`, `UPDATING=False`, `DEGRADED=False` and fully ready/updated node counts. The [fresh-lab runbook](01-FRESH-LAB-RUNBOOK.md#step-2--fresh-openshift-health-gate-read-only) includes a machine-readable, read-only check that fails if these conditions aren't met.

## 3. Confirm the extracted installer

If you completed the **first two steps above**, the files are already in `~/fusion-lab01-installer` and no additional upload is needed.

```bash
cd ~/fusion-lab01-installer
ls -lah
```

Keep the installer separate from the historic `~/fusion-automation` project. `plan` creates a separate, cluster-pinned `work/<cluster>/` folder.

## 4. Verify utilities

```bash
command -v oc
command -v ansible-playbook
command -v ansible-vault
command -v jq
python3 -c 'import yaml; print("PyYAML available")'
```

**Important:** On the first `deploy`, the v2.1 installer prompts for the Scale GUI username (Enter accepts `csi-storage-gui-user`) and a hidden password. Both are encrypted using Ansible Vault; a random local-only key and the encrypted values are stored in separate directories outside the repository under `~/.config/fusion-lab01/`. Neither is uploaded to GitHub. Do not store private kubeconfig or Vault data in your Git working tree.
