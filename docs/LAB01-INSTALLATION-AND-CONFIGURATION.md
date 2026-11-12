# Lab 1 — Installation and Configuration

[Project home](../README.md) · [Starting without Ansible?](GETTING-STARTED-FROM-ZERO.md) · [Scale troubleshooting and recovery](LAB01-SCALE-TROUBLESHOOTING.md)

This is the **complete, step-by-step Quick Start** for the supported IBM Fusion Level 4 Lab 1 installation and persistent-storage workflow. It assumes an existing Ubuntu Ansible control node; the first step also shows how to get the packaged installer onto it.

**What this does:** The `plan` command **checks lab readiness without changing cluster resources**; the `deploy` command **runs the Ansible automation** to install and verify the supported IBM Fusion, Fusion Data Foundation/Ceph, and external IBM Storage Scale portions of Lab 1. 

**Before downloading the installer:** Reserve **IBM Fusion on OpenShift Virtualization** using the [Lab 1 TechZone configuration settings](GETTING-STARTED-FROM-ZERO.md#3-make-a-fresh-techzone-reservation) (OCP 4.21, three worker nodes, and the selected 16 vCPU/64 GB/300 GB worker flavor).

**Starting without an Ansible server?** Follow [Getting Started from Zero](GETTING-STARTED-FROM-ZERO.md) first. The instructions below assume an Ubuntu automation host with Python, Ansible, OpenShift CLI (`oc`), SSH, and a current TechZone reservation. These instructions are for a **disposable lab, not production**.

## What Lab 1 automates

```mermaid
flowchart TD
    A[Verify OpenShift cluster] --> B[Install IBM Fusion and Ceph storage]
    B --> C[Test Ceph persistent storage]
    C --> D[Prepare Scale workers and deploy client]
    D --> E[Connect to existing external Scale filesystem]
    E --> F[Test Scale persistence and verify installation]
```

The workflow configures IBM Fusion Data Foundation, a three-node local Ceph storage cluster, and a three-node IBM Storage Scale data-access client. It connects to the predeployed Scale filesystem and creates the `fusionfs1` StorageClass. Both backends are tested for persistent data across pod replacement using SHA-256 verification.

### Step 1 — Download and install the Ansible scripts on Ubuntu

1. On your Windows PC, open [GitHub Releases](https://github.com/ryanbeaty-ibm/ibm-fusion-techzone-automation/releases). Open **IBM Fusion Lab 1 — Ansible Installer v2.4 (pre-release)**.
2. Under **Assets**, download **`IBM-Fusion-Lab01-OneCommand-v2.4.zip`** to `C:\Users\YOUR_USERNAME\Downloads`. **Do not use** GitHub's automatically generated **Source code (zip)**; it is not the packaged installer asset.
3. Open a **SecureCRT Secure File Transfer Protocol (SFTP)** session to the Ubuntu VM. For the documented Ubuntu `automation` account, enter:

   ```text
   lcd C:\Users\YOUR_USERNAME\Downloads
   cd /home/automation
   put IBM-Fusion-Lab01-OneCommand-v2.4.zip
   ```

   **Note:** `/home/automation` is the home directory for the Ubuntu user `automation` in our prerequisites guide. If your Ansible server uses a different account, replace `automation` with its username (for example, `/home/john`).

4. In your **Ubuntu SSH session**, extract and open the installer directory (run these in Ubuntu, not PowerShell):

   ```bash
   mkdir -p "$HOME/fusion-lab01-v2.4"
   unzip -o "$HOME/IBM-Fusion-Lab01-OneCommand-v2.4.zip" -d "$HOME/fusion-lab01-v2.4"
   cd "$HOME/fusion-lab01-v2.4"
   ls -l install-lab01.sh
   ```

### Step 2 — Download and transfer your TechZone kubeconfig

1. Open your **TechZone reservation**.
2. Under **Download kubeconfig**, click **Download**.
3. Name the downloaded file for your lab, for example **`lab01.conf`**, and save it to `C:\Users\YOUR_USERNAME\Downloads`. Keep it **outside the Git repository**.
4. On Ubuntu, create a protected directory before transferring:

   ```bash
   mkdir -p "$HOME/.kube" && chmod 700 "$HOME/.kube"
   ```

5. In your **SecureCRT SFTP session**, run:

   ```text
   lcd C:\Users\YOUR_USERNAME\Downloads
   cd /home/automation/.kube
   put lab01.conf
   ```

6. Back in **Ubuntu SSH**, protect and test the file:

   ```bash
   chmod 600 "$HOME/.kube/lab01.conf"
   oc --kubeconfig="$HOME/.kube/lab01.conf" whoami --show-server
   oc --kubeconfig="$HOME/.kube/lab01.conf" get nodes
   ```

   Use your own filename in all subsequent commands. The output should identify the expected reservation's OpenShift Container Platform (OCP) API server.

### Step 3 — Obtain the lab values you will enter

1. Open your IBM TechZone reservation, scroll down to **Environments**, and expand **IBM Fusion on OpenShift Virtualization**. Under **OUTPUTS**, locate **Environment ID** (example `itz-REPLACE_ME`). This is `--cluster`.
2. Under **OUTPUTS**, click **VM Remote Console**. Find the existing **`xxx-scale-2` / `xxx-scale-02`** virtual machine, and note its **IP Address**. This is `--scale-host` (the lab guide commonly shows `10.10.10.202`). The Scale VM is already deployed; the installer does **not** create it.
3. In the IBM Fusion Installation and Configuration lab guide, see labeled **pages 30 and 76** for the **IBM Storage Scale GUI / REST API username and password**. The installer normally suggests username `csi-storage-gui-user`. You will enter its matching password privately during deployment; **do not add it to a Git file**.
   **Need to log into the existing Scale Linux VM for troubleshooting?** Select the VM in **VM Remote Console**, click **Console** and use **RDP** with username `itzuser` and the **Bastion Password** from the reservation **Outputs**. This is **not** the Scale GUI password and `kubeadmin` is for OpenShift. See [Scale connectivity and credential troubleshooting](LAB01-SCALE-TROUBLESHOOTING.md).

### Step 4 — Validate your lab (read-only preflight check)

Run from the extracted Ubuntu directory. **Replace the placeholders with your reservation's actual values**:

```bash
bash install-lab01.sh plan \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/REPLACE_ME.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde
```

`REPLACE_ME.conf` is the filename you uploaded (for example, `lab01.conf`). The plan checks OCP version and health, ClusterOperators, MachineConfigPools, the selected target, and stage order. **It does not install anything or modify cluster resources.** Disk eligibility is checked immediately before Ceph claims during deployment; new or updated Scale GUI credentials are checked from an OpenShift worker early during `deploy` before the storage stages. Confirm the displayed target before proceeding.

### Step 5 — Deploy Lab 1 (execute the Ansible automation)

**Warning: This command makes real cluster changes.** Confirm that the cluster is disposable and `/dev/vde` (or your selected disk) is intended to be erased on all three Ceph infrastructure nodes. The script may also reboot worker nodes.

```bash
bash install-lab01.sh deploy \
  --cluster itz-REPLACE_ME \
  --kubeconfig "$HOME/.kube/REPLACE_ME.conf" \
  --scale-host REPLACE_WITH_EXISTING_SCALE_IP \
  --ceph-disk /dev/vde \
  --claim-disks \
  --allow-worker-reboots
```

**Interactive Scale credentials (new in v2.4):**

1. At `Scale GUI username [csi-storage-gui-user]:`, press **Enter** to accept the default, or type your assigned GUI user.
2. At `Scale GUI password (hidden):`, type the GUI password from the lab guide and press **Enter**.
3. At `Confirm Scale GUI password (hidden):`, **type that password a second time** and press **Enter**. Neither entry appears as you type.
4. If the entries do not match, re-enter both; the installer allows **three attempts** and stops without saving the new credentials if they still differ.
5. After a match, the installer performs a **read-only, early Scale GUI authentication test from a temporary OpenShift worker debug pod**. This is necessary because the Ubuntu control node cannot normally reach the private Scale IP. **HTTP 200** is required before new credentials are encrypted and deployment begins. HTTP 401/403 stops immediately with a clear message. The temporary debug pod changes no persistent cluster storage, but requires permission to debug a node.

If you are **reusing previously saved encrypted credentials**, the installer does not prompt or rerun this early check by default. Use `--update-scale-credentials` to re-enter, reconfirm, and test them. The early GET check confirms authentication to `/scalemgmt/v2/info`; remote registration permissions are verified later during the Scale connection stage.

The credentials remain outside the Git repository in a user-only **Ansible Vault** file. Never paste passwords into GitHub, terminal commands, or published logs.

### Step 6 — Monitor and verify deployment

**Plan on roughly 40 minutes for a healthy environment**; timing varies and a failed authentication wait can add up to 30 minutes. Leave Ubuntu SSH connected, watch the Ansible stages, and do not interrupt long-running tasks merely because output pauses. The workflow runs `fusion-ceph`, `ceph-io-test`, `scale-nodeprep`, `scale-operator`, `scale-client`, `scale-external`, and `final-verification`.

A successful run ends with `PASS: ALL LAB 01 INSTALLATION AND STORAGE TEST STAGES.` This covers the supported **installation and persistent-storage** portion of Lab 1, not every workbook exercise. The Scale test also proves volume provisioning, write, remount, checksum, and cleanup.

**Recovery from a wrong Scale GUI password:** If only `scale-external` failed and the earlier stages passed, see [Scale troubleshooting and resume](LAB01-SCALE-TROUBLESHOOTING.md). Do **not** reinstall Fusion or Ceph. The v2.4 resume command still requires both authorization flags **even when resuming a later stage**.

**Validation status:** **v2.4 is an unvalidated pre-release candidate** (offline tests only, including password confirmation and a mocked early API test). The prior v2.3 passed on a fresh OCP 4.21.24 TechZone cluster on **November 12, 2026**, **after correcting a mistyped Scale GUI password and resuming from `scale-external`**. This was a validated recovery, **not** an uninterrupted first-attempt deployment. See [the v2.3 validation record](07-LIVE-VALIDATION-2026-11-12.md) and [the original v2.2 validation record](../VALIDATED-LAB01-RESULT.md).
