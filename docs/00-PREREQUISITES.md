# 00 — Prerequisites, SFTP and kubeconfig

## Requirements: verified vs. assumed

The **v2.3 workflow** checks these prerequisites automatically at the appropriate stage (some are verified by the launcher, some during deployment):

- IBM TechZone OpenShift Container Platform (OCP) **4.21.x** environment, with exactly **3 masters, 3 infrastructure workers, and 3 regular workers**.
- Cluster node names follow the `itz-XXXXXX-{master,infra,worker}-{1,2,3}` convention; all must be Ready.
- A functioning `oc` client and an explicit, named kubeconfig whose identity is `system:admin`.
- Existing, **pre-deployed external IBM Storage Scale server** accessible from the cluster, with filesystem `fs1`.
- A reviewed, blank nonrotational storage disk on each infrastructure node; the known example was `/dev/vde` and the installer requires at least 400 GB per disk.
- An Ubuntu automation host with `bash`, `unzip`, `oc`, `ansible-playbook`, `ansible-vault`, `jq`, `python3` with the PyYAML package, and standard Linux utilities.

The program does **not** install these dependencies for you, test external Scale network connectivity during `plan`, or confirm that a candidate disk is empty during `plan`. Disk qualification occurs in the deployment stages.

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

## 3. Transfer and extract the installer

Put `IBM-Fusion-Lab01-OneCommand-v2.3.zip` in `D:\Dropbox\Fusion`, then SecureCRT SFTP:

```text
lcd D:\Dropbox\Fusion
cd /home/automation
put IBM-Fusion-Lab01-OneCommand-v2.3.zip
```

Ubuntu SSH:

```bash
mkdir -p "$HOME/fusion-lab01-installer"
cd "$HOME/fusion-lab01-installer"
unzip -o "$HOME/IBM-Fusion-Lab01-OneCommand-v2.3.zip" -d .
```

Do not extract into an old per-lab working directory; keep a separate, versioned source folder. A new workspace will be created under `work/<new-cluster-prefix>/` during `plan`.

## 4. Verify utilities

```bash
command -v oc
command -v ansible-playbook
command -v ansible-vault
command -v jq
python3 -c 'import yaml; print("PyYAML available")'
```

**Important:** On the first `deploy`, the v2.3 installer prompts for the Scale GUI username (Enter accepts `csi-storage-gui-user`) and a hidden password. Both are encrypted using Ansible Vault; a random local-only key and the encrypted values are stored in separate directories outside the repository under `~/.config/fusion-lab01/`. Neither is uploaded to GitHub. Do not store private kubeconfig or Vault data in your Git working tree.

## Automatic health gate in v2.3

Both `plan` and `deploy` run a read-only `installer/cluster-health.yml` Ansible
preflight. It verifies the OpenShift ClusterVersion, every ClusterOperator, and
all MachineConfigPools. If any is unhealthy, **the installer stops before
applying any resources**. The existing Ceph disk qualification occurs immediately
before disk claims; the external Scale connection stage validates that server.
